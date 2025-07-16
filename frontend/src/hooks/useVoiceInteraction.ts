import { useEffect, useRef, useState, useCallback } from 'react';
import { useWebSocket } from '../contexts/WebSocketContext';
import { useAppState } from '../contexts/AppStateContext';

interface UseVoiceInteractionOptions {
  continuous?: boolean;
  wakeWord?: string;
}

export const useVoiceInteraction = (options: UseVoiceInteractionOptions = {}) => {
  const { continuous = true, wakeWord = 'hey jarvis' } = options;
  const { sendMessage, onMessage, connected } = useWebSocket();
  const { setListening, setSpeaking, setThinking } = useAppState();
  
  const [isActive, setIsActive] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [error, setError] = useState<string | null>(null);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const animationFrameRef = useRef<number | null>(null);

  // Initialize audio context
  useEffect(() => {
    audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
    return () => {
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, []);

  // Monitor audio levels
  const monitorAudioLevel = useCallback(() => {
    if (!analyserRef.current || !isActive) return;
    
    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
    analyserRef.current.getByteFrequencyData(dataArray);
    const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
    setAudioLevel(average / 255);
    
    animationFrameRef.current = requestAnimationFrame(monitorAudioLevel);
  }, [isActive]);

  // Start audio capture
  const startCapture = useCallback(async () => {
    try {
      setError(null);
      
      // Request microphone permission
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000, // 16kHz for wake word detection
        } 
      });
      
      streamRef.current = stream;
      setIsActive(true);
      
      // Set up audio analysis
      if (audioContextRef.current) {
        const source = audioContextRef.current.createMediaStreamSource(stream);
        analyserRef.current = audioContextRef.current.createAnalyser();
        analyserRef.current.fftSize = 256;
        source.connect(analyserRef.current);
        monitorAudioLevel();
      }

      // Set up media recorder for continuous streaming
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus') 
        ? 'audio/webm;codecs=opus' 
        : 'audio/webm';
        
      const mediaRecorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      // Stream audio chunks to server
      mediaRecorder.ondataavailable = async (event) => {
        if (event.data.size > 0 && connected) {
          // Convert to base64 and send immediately for real-time processing
          const arrayBuffer = await event.data.arrayBuffer();
          const uint8Array = new Uint8Array(arrayBuffer);
          const base64 = btoa(String.fromCharCode.apply(null, Array.from(uint8Array)));
          
          sendMessage({ 
            type: 'audio_stream',
            audio: base64,
            mimeType: mimeType,
            timestamp: Date.now()
          });
          
          // Also keep chunks for potential batch processing
          chunksRef.current.push(event.data);
        }
      };

      // Start recording with small time slices for near real-time streaming
      mediaRecorder.start(100); // Send chunks every 100ms
      
      // Notify backend that audio streaming has started
      sendMessage({
        type: 'audio_stream_start',
        sampleRate: 16000,
        mimeType: mimeType
      });
      
    } catch (err) {
      console.error('Error starting audio capture:', err);
      setError(err instanceof Error ? err.message : 'Failed to start audio capture');
      setIsActive(false);
    }
  }, [connected, sendMessage, monitorAudioLevel]);

  // Stop audio capture
  const stopCapture = useCallback(() => {
    setIsActive(false);
    setAudioLevel(0);

    // Stop animation frame
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }

    // Stop media recorder
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current = null;
    }

    // Stop all tracks
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }

    // Notify backend
    if (connected) {
      sendMessage({ type: 'audio_stream_stop' });
    }
  }, [connected, sendMessage]);

  // Manual trigger for push-to-talk mode
  const triggerVoiceInput = useCallback(async () => {
    if (!isActive) {
      await startCapture();
    }
    
    // Send trigger event
    sendMessage({ type: 'voice_trigger', source: 'button' });
    setListening(true);
  }, [isActive, startCapture, sendMessage, setListening]);

  // Handle WebSocket messages
  useEffect(() => {
    const unsubscribeWakeWord = onMessage('wake_word_detected', (data) => {
      console.log('Wake word detected:', data);
      setListening(true);
    });

    const unsubscribeVoiceState = onMessage('voice_state', (data) => {
      const state = data.state;
      setListening(state === 'listening' || state === 'recording');
      setThinking(state === 'processing');
      setSpeaking(state === 'speaking');
    });

    const unsubscribeError = onMessage('audio_error', (data) => {
      console.error('Audio error:', data.message);
      setError(data.message);
    });

    return () => {
      unsubscribeWakeWord();
      unsubscribeVoiceState();
      unsubscribeError();
    };
  }, [onMessage, setListening, setThinking, setSpeaking]);

  // Start continuous capture on mount if enabled
  useEffect(() => {
    if (continuous && connected) {
      startCapture();
    }
    
    return () => {
      stopCapture();
    };
  }, [continuous, connected]); // eslint-disable-line react-hooks/exhaustive-deps

  return {
    isActive,
    audioLevel,
    error,
    startCapture,
    stopCapture,
    triggerVoiceInput,
  };
};