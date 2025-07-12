"""
Audio processor with noise cancellation and voice activity detection
"""

import numpy as np
import sounddevice as sd
import webrtcvad
import scipy.signal
from collections import deque
from typing import Optional, Tuple, List
import threading
import queue
import logging

logger = logging.getLogger(__name__)

class AudioProcessor:
    """Handles audio processing with noise cancellation and VAD"""
    
    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        frame_duration_ms: int = 30,
        vad_aggressiveness: int = 3,
        noise_reduction_strength: float = 0.8
    ):
        """
        Initialize audio processor
        
        Args:
            sample_rate: Audio sample rate (Hz)
            channels: Number of audio channels
            frame_duration_ms: Frame duration for VAD (10, 20, or 30 ms)
            vad_aggressiveness: VAD aggressiveness (0-3, higher = more aggressive)
            noise_reduction_strength: Noise reduction strength (0-1)
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.frame_duration_ms = frame_duration_ms
        self.noise_reduction_strength = noise_reduction_strength
        
        # Initialize VAD
        self.vad = webrtcvad.Vad(vad_aggressiveness)
        
        # Frame size in samples
        self.frame_size = int(sample_rate * frame_duration_ms / 1000)
        
        # Audio buffers
        self.audio_buffer = deque(maxlen=int(sample_rate * 2))  # 2 seconds
        self.noise_profile = None
        self.noise_estimation_frames = 30  # Frames to estimate noise
        
        # Processing queue
        self.processing_queue = queue.Queue()
        self.is_recording = False
        
        logger.info(f"AudioProcessor initialized: {sample_rate}Hz, {channels}ch, {frame_duration_ms}ms frames")
    
    def estimate_noise_profile(self, audio_data: np.ndarray) -> np.ndarray:
        """Estimate noise profile from audio data"""
        # Use first 0.5 seconds for noise estimation
        noise_samples = int(self.sample_rate * 0.5)
        if len(audio_data) < noise_samples:
            # For short segments, return a simple noise estimate
            return np.ones(129) * np.mean(np.abs(audio_data))  # Default FFT size
        
        noise_segment = audio_data[:noise_samples]
        
        # Compute power spectral density
        nperseg = min(256, len(noise_segment))
        frequencies, psd = scipy.signal.welch(
            noise_segment,
            self.sample_rate,
            nperseg=nperseg
        )
        
        return psd
    
    def apply_noise_reduction(self, audio_data: np.ndarray) -> np.ndarray:
        """Apply spectral subtraction noise reduction"""
        if self.noise_profile is None:
            # Estimate noise on first call
            self.noise_profile = self.estimate_noise_profile(audio_data)
        
        # Adjust STFT parameters based on frame size
        nperseg = min(256, len(audio_data))
        noverlap = nperseg // 2
        
        # Apply spectral subtraction
        # Convert to frequency domain
        stft = scipy.signal.stft(
            audio_data,
            self.sample_rate,
            nperseg=nperseg,
            noverlap=noverlap
        )[2]
        
        # Compute magnitude and phase
        magnitude = np.abs(stft)
        phase = np.angle(stft)
        
        # Estimate noise floor
        # Ensure noise profile matches the magnitude shape
        if len(self.noise_profile) >= magnitude.shape[0]:
            noise_floor = np.sqrt(self.noise_profile[:magnitude.shape[0], np.newaxis])
        else:
            # Interpolate noise profile if needed
            noise_floor = np.sqrt(np.interp(
                np.linspace(0, 1, magnitude.shape[0]),
                np.linspace(0, 1, len(self.noise_profile)),
                self.noise_profile
            ))[:, np.newaxis]
        
        # Spectral subtraction
        clean_magnitude = magnitude - self.noise_reduction_strength * noise_floor
        clean_magnitude = np.maximum(clean_magnitude, 0.1 * magnitude)  # Prevent over-subtraction
        
        # Reconstruct signal
        clean_stft = clean_magnitude * np.exp(1j * phase)
        _, clean_audio = scipy.signal.istft(
            clean_stft,
            self.sample_rate,
            nperseg=nperseg,
            noverlap=noverlap
        )
        
        return clean_audio[:len(audio_data)]
    
    def apply_preprocessing(self, audio_data: np.ndarray) -> np.ndarray:
        """Apply audio preprocessing (filtering, normalization)"""
        # High-pass filter to remove low-frequency noise
        nyquist = self.sample_rate / 2
        cutoff = 80  # Hz
        
        b, a = scipy.signal.butter(
            4,
            cutoff / nyquist,
            btype='high'
        )
        filtered = scipy.signal.filtfilt(b, a, audio_data)
        
        # Normalize audio
        max_val = np.max(np.abs(filtered))
        if max_val > 0:
            normalized = filtered / max_val * 0.8  # Leave headroom
        else:
            normalized = filtered
        
        return normalized
    
    def process_frame(self, frame: bytes) -> Tuple[bool, np.ndarray]:
        """
        Process a single audio frame
        
        Returns:
            Tuple of (is_speech, processed_audio)
        """
        # Convert bytes to numpy array
        audio_data = np.frombuffer(frame, dtype=np.int16).astype(np.float32) / 32768.0
        
        # Apply preprocessing
        preprocessed = self.apply_preprocessing(audio_data)
        
        # Apply noise reduction
        clean_audio = self.apply_noise_reduction(preprocessed)
        
        # Check for speech using VAD
        # VAD requires 16-bit PCM
        vad_frame = (clean_audio * 32768).astype(np.int16).tobytes()
        is_speech = self.vad.is_speech(vad_frame, self.sample_rate)
        
        return is_speech, clean_audio
    
    def process_audio_stream(self, callback=None):
        """Start processing audio stream with callback"""
        def audio_callback(indata, frames, time, status):
            if status:
                logger.warning(f"Audio status: {status}")
            
            # Process audio
            audio_frame = indata[:, 0] if self.channels > 1 else indata.flatten()
            
            # Convert to bytes for VAD
            frame_bytes = (audio_frame * 32768).astype(np.int16).tobytes()
            
            # Process frame
            is_speech, clean_audio = self.process_frame(frame_bytes)
            
            # Add to buffer if speech detected
            if is_speech:
                self.audio_buffer.extend(clean_audio)
                
                if callback:
                    callback(clean_audio, is_speech)
        
        # Start audio stream
        self.stream = sd.InputStream(
            callback=audio_callback,
            channels=self.channels,
            samplerate=self.sample_rate,
            blocksize=self.frame_size
        )
        
        self.stream.start()
        self.is_recording = True
        logger.info("Audio processing started")
    
    def stop_processing(self):
        """Stop audio processing"""
        if hasattr(self, 'stream') and self.stream.active:
            self.stream.stop()
            self.stream.close()
            self.is_recording = False
            logger.info("Audio processing stopped")
    
    def get_audio_buffer(self) -> np.ndarray:
        """Get current audio buffer"""
        return np.array(self.audio_buffer)
    
    def clear_buffer(self):
        """Clear audio buffer"""
        self.audio_buffer.clear()

class BeamformingProcessor(AudioProcessor):
    """Audio processor with beamforming for multi-microphone arrays"""
    
    def __init__(self, mic_positions: List[Tuple[float, float, float]], **kwargs):
        """
        Initialize beamforming processor
        
        Args:
            mic_positions: List of (x, y, z) microphone positions in meters
            **kwargs: Additional arguments for AudioProcessor
        """
        super().__init__(**kwargs)
        self.mic_positions = np.array(mic_positions)
        self.num_mics = len(mic_positions)
        
        # Beamforming parameters
        self.sound_speed = 343  # m/s
        self.target_direction = np.array([0, 0, 1])  # Default: straight ahead
        
    def calculate_delays(self, direction: np.ndarray) -> np.ndarray:
        """Calculate time delays for beamforming"""
        # Calculate distances from each mic to source
        delays = []
        for mic_pos in self.mic_positions:
            distance = np.dot(mic_pos, direction)
            delay = distance / self.sound_speed
            delays.append(delay)
        
        # Normalize to smallest delay
        delays = np.array(delays)
        delays -= np.min(delays)
        
        return delays
    
    def apply_beamforming(self, multi_channel_audio: np.ndarray) -> np.ndarray:
        """Apply delay-and-sum beamforming"""
        if multi_channel_audio.shape[1] != self.num_mics:
            logger.warning("Channel count mismatch for beamforming")
            return multi_channel_audio[:, 0]  # Return first channel
        
        # Calculate delays
        delays = self.calculate_delays(self.target_direction)
        
        # Apply delays and sum
        output = np.zeros(len(multi_channel_audio))
        for i, delay in enumerate(delays):
            # Convert delay to samples
            delay_samples = int(delay * self.sample_rate)
            
            # Apply delay
            if delay_samples > 0:
                channel_data = np.pad(
                    multi_channel_audio[:, i],
                    (delay_samples, 0),
                    mode='constant'
                )[:len(output)]
            else:
                channel_data = multi_channel_audio[:, i]
            
            output += channel_data
        
        # Normalize
        output /= self.num_mics
        
        return output