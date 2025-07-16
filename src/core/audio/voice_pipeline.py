"""
Voice Pipeline - Connects wake word detection, STT, LLM, and TTS
This module orchestrates the complete voice interaction flow
"""

import asyncio
import logging
from enum import Enum
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
import time
import numpy as np

from src.core.audio.openwakeword_detector import ContinuousOpenWakeWordListener
from src.core.audio.audio_processor import AudioProcessor
from src.models.speech_to_text import SpeechToText
from src.core.llm.companion_llm import CompanionLLM
from src.core.audio.tts_engine import PiperTTSEngine
from src.core.hardware.hardware_manager import HardwareManager

logger = logging.getLogger(__name__)


class PipelineState(Enum):
    """States of the voice pipeline"""
    IDLE = "idle"
    LISTENING_FOR_WAKE = "listening_for_wake"
    RECORDING = "recording"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    ERROR = "error"


@dataclass
class VoiceInteraction:
    """Represents a complete voice interaction"""
    wake_word_detected: bool = False
    wake_word_timestamp: Optional[float] = None
    audio_data: Optional[np.ndarray] = None
    transcript: Optional[str] = None
    response: Optional[str] = None
    audio_response: Optional[bytes] = None
    error: Optional[str] = None
    duration: Optional[float] = None


class VoicePipeline:
    """Main voice pipeline orchestrator"""
    
    def __init__(
        self,
        mode: str = "friend",
        user_id: Optional[int] = None,
        on_state_change: Optional[Callable[[PipelineState, Dict[str, Any]], None]] = None,
        on_transcript: Optional[Callable[[str], None]] = None,
        on_response: Optional[Callable[[str], None]] = None
    ):
        """
        Initialize the voice pipeline
        
        Args:
            mode: Interaction mode (tutor/friend/hybrid)
            user_id: User ID for personalization
            on_state_change: Callback for state changes
            on_transcript: Callback when transcript is ready
            on_response: Callback when response is ready
        """
        self.mode = mode
        self.user_id = user_id
        self.state = PipelineState.IDLE
        self._running = False
        
        # Callbacks
        self.on_state_change = on_state_change
        self.on_transcript = on_transcript
        self.on_response = on_response
        
        # Initialize components
        self.hardware = HardwareManager()
        self.wake_word_detector = None
        self.audio_processor = AudioProcessor()
        self.stt = SpeechToText()
        self.llm = CompanionLLM()  # Mode is passed to generate_response, not constructor
        self.tts = PiperTTSEngine()
        
        # Audio recording buffer
        self.recording_buffer = []
        self.recording_start_time = None
        self.max_recording_duration = 10.0  # seconds
        self.silence_threshold = 2.0  # seconds of silence to stop recording
        
        logger.info(f"Voice pipeline initialized in {mode} mode")
    
    def _change_state(self, new_state: PipelineState, data: Optional[Dict[str, Any]] = None):
        """Change pipeline state and notify"""
        self.state = new_state
        
        # Update hardware LEDs based on state
        if self.hardware.led_controller:
            state_patterns = {
                PipelineState.IDLE: "idle",
                PipelineState.LISTENING_FOR_WAKE: "idle",
                PipelineState.RECORDING: "listening",
                PipelineState.PROCESSING: "thinking",
                PipelineState.SPEAKING: "speaking",
                PipelineState.ERROR: "error"
            }
            pattern = state_patterns.get(new_state, "idle")
            self.hardware.led_controller.set_pattern(pattern)
        
        # Notify callback
        if self.on_state_change:
            self.on_state_change(new_state, data or {})
        
        logger.info(f"Pipeline state changed to: {new_state.value}")
    
    async def start(self):
        """Start the voice pipeline"""
        if self._running:
            logger.warning("Pipeline already running")
            return
        
        self._running = True
        self._change_state(PipelineState.LISTENING_FOR_WAKE)
        
        # Initialize wake word detector
        self.wake_word_detector = ContinuousOpenWakeWordListener(
            on_detection=self._on_wake_word_detected
        )
        
        # Start wake word detection
        self.wake_word_detector.start()
        
        # Set up hardware button handler
        if self.hardware.button_manager:
            self.hardware.button_manager.on_wake = self._on_wake_word_detected
        
        logger.info("Voice pipeline started")
    
    async def stop(self):
        """Stop the voice pipeline"""
        self._running = False
        
        # Stop wake word detector
        if self.wake_word_detector:
            self.wake_word_detector.stop()
        
        # Stop hardware
        self.hardware.cleanup()
        
        self._change_state(PipelineState.IDLE)
        logger.info("Voice pipeline stopped")
    
    def _on_wake_word_detected(self, model_id: Optional[str] = None):
        """Handle wake word detection"""
        if self.state != PipelineState.LISTENING_FOR_WAKE:
            logger.debug("Wake word detected but pipeline not listening")
            return
        
        logger.info(f"Wake word detected: {model_id or 'button'}")
        
        # Start recording
        asyncio.create_task(self._start_recording())
    
    async def _start_recording(self):
        """Start recording user speech"""
        self._change_state(PipelineState.RECORDING)
        
        self.recording_buffer = []
        self.recording_start_time = time.time()
        
        # Stop wake word detection during recording
        if self.wake_word_detector:
            self.wake_word_detector.pause()
        
        # Start audio recording with VAD
        try:
            audio_data = await self._record_with_vad()
            
            if audio_data is not None and len(audio_data) > 0:
                await self._process_audio(audio_data)
            else:
                logger.warning("No audio recorded")
                self._change_state(PipelineState.LISTENING_FOR_WAKE)
                if self.wake_word_detector:
                    self.wake_word_detector.resume()
        
        except Exception as e:
            logger.error(f"Recording error: {e}")
            self._handle_error(str(e))
    
    async def _record_with_vad(self) -> Optional[np.ndarray]:
        """Record audio with voice activity detection"""
        import sounddevice as sd
        
        # Recording parameters
        sample_rate = 16000
        channels = 1
        chunk_duration = 0.1  # 100ms chunks
        chunk_size = int(sample_rate * chunk_duration)
        
        # VAD state
        silence_chunks = 0
        speech_detected = False
        max_silence_chunks = int(self.silence_threshold / chunk_duration)
        
        # Create audio stream
        stream = sd.InputStream(
            samplerate=sample_rate,
            channels=channels,
            dtype='float32'
        )
        
        try:
            stream.start()
            
            while self._running and self.state == PipelineState.RECORDING:
                # Check max duration
                if time.time() - self.recording_start_time > self.max_recording_duration:
                    logger.info("Max recording duration reached")
                    break
                
                # Read audio chunk
                audio_chunk, _ = stream.read(chunk_size)
                audio_chunk = audio_chunk.flatten()
                
                # Process with VAD
                processed_chunk = self.audio_processor.process_audio(audio_chunk)
                
                # Check if speech detected
                if self.audio_processor.vad.process(stream, audio_chunk).is_speech:
                    silence_chunks = 0
                    speech_detected = True
                    self.recording_buffer.append(processed_chunk)
                else:
                    silence_chunks += 1
                    if speech_detected:
                        self.recording_buffer.append(processed_chunk)
                    
                    # Stop if enough silence after speech
                    if speech_detected and silence_chunks >= max_silence_chunks:
                        logger.info("Silence detected, stopping recording")
                        break
            
            stream.stop()
            
            # Combine audio chunks
            if self.recording_buffer:
                audio_data = np.concatenate(self.recording_buffer)
                return audio_data
            else:
                return None
        
        except Exception as e:
            logger.error(f"Recording error: {e}")
            if stream.active:
                stream.stop()
            raise
        finally:
            stream.close()
    
    async def _process_audio(self, audio_data: np.ndarray):
        """Process recorded audio through STT → LLM → TTS"""
        self._change_state(PipelineState.PROCESSING)
        
        interaction = VoiceInteraction(
            wake_word_detected=True,
            wake_word_timestamp=self.recording_start_time,
            audio_data=audio_data
        )
        
        try:
            # Speech to text
            logger.info("Transcribing audio...")
            transcript = await asyncio.to_thread(
                self.stt.transcribe, 
                audio_data
            )
            
            if not transcript:
                raise ValueError("No speech detected in audio")
            
            interaction.transcript = transcript
            logger.info(f"Transcript: {transcript}")
            
            # Notify transcript callback
            if self.on_transcript:
                self.on_transcript(transcript)
            
            # Get LLM response
            logger.info("Getting LLM response...")
            response = await asyncio.to_thread(
                self.llm.get_response,
                transcript,
                user_id=self.user_id
            )
            
            interaction.response = response
            logger.info(f"Response: {response}")
            
            # Notify response callback
            if self.on_response:
                self.on_response(response)
            
            # Generate TTS audio
            logger.info("Generating speech...")
            audio_response = await self.tts.synthesize_async(response)
            
            if audio_response:
                interaction.audio_response = audio_response
                await self._play_response(audio_response)
            
            # Calculate total duration
            interaction.duration = time.time() - self.recording_start_time
            logger.info(f"Interaction completed in {interaction.duration:.2f}s")
            
        except Exception as e:
            logger.error(f"Processing error: {e}")
            interaction.error = str(e)
            self._handle_error(str(e))
        
        finally:
            # Resume listening
            self._change_state(PipelineState.LISTENING_FOR_WAKE)
            if self.wake_word_detector:
                self.wake_word_detector.resume()
    
    async def _play_response(self, audio_data: bytes):
        """Play TTS audio response"""
        self._change_state(PipelineState.SPEAKING)
        
        try:
            import sounddevice as sd
            import io
            import wave
            
            # Read WAV data
            with io.BytesIO(audio_data) as wav_buffer:
                with wave.open(wav_buffer, 'rb') as wav_file:
                    sample_rate = wav_file.getframerate()
                    channels = wav_file.getnchannels()
                    audio_array = np.frombuffer(
                        wav_file.readframes(wav_file.getnframes()),
                        dtype=np.int16
                    ).astype(np.float32) / 32768.0
            
            # Play audio
            await asyncio.to_thread(
                sd.play,
                audio_array,
                sample_rate,
                blocking=True
            )
            
        except Exception as e:
            logger.error(f"Playback error: {e}")
            raise
    
    def _handle_error(self, error_message: str):
        """Handle pipeline errors"""
        self._change_state(PipelineState.ERROR, {"error": error_message})
        
        # Brief error state then resume
        asyncio.create_task(self._recover_from_error())
    
    async def _recover_from_error(self):
        """Recover from error state"""
        await asyncio.sleep(2.0)
        self._change_state(PipelineState.LISTENING_FOR_WAKE)
        if self.wake_word_detector:
            self.wake_word_detector.resume()
    
    def set_mode(self, mode: str):
        """Change interaction mode"""
        self.mode = mode
        if self.llm:
            self.llm.mode = mode
        logger.info(f"Mode changed to: {mode}")
    
    async def process_text_input(self, text: str) -> str:
        """Process text input directly (for testing or text interface)"""
        try:
            # Get LLM response
            response = await asyncio.to_thread(
                self.llm.get_response,
                text,
                user_id=self.user_id
            )
            
            # Generate TTS if pipeline is running
            if self._running:
                audio_response = await self.tts.synthesize_async(response)
                if audio_response:
                    await self._play_response(audio_response)
            
            return response
            
        except Exception as e:
            logger.error(f"Text processing error: {e}")
            return f"Sorry, I encountered an error: {str(e)}"


# Convenience function for testing
async def test_pipeline():
    """Test the voice pipeline"""
    import signal
    
    # Create pipeline
    pipeline = VoicePipeline(
        mode="friend",
        on_state_change=lambda state, data: print(f"State: {state.value}", data),
        on_transcript=lambda text: print(f"You said: {text}"),
        on_response=lambda text: print(f"Assistant: {text}")
    )
    
    # Handle shutdown
    def shutdown(sig, frame):
        print("\nShutting down...")
        asyncio.create_task(pipeline.stop())
    
    signal.signal(signal.SIGINT, shutdown)
    
    # Start pipeline
    print("Starting voice pipeline... Say 'Hey Jarvis' to activate")
    await pipeline.start()
    
    # Keep running
    try:
        while pipeline._running:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        pass
    
    await pipeline.stop()


if __name__ == "__main__":
    asyncio.run(test_pipeline())