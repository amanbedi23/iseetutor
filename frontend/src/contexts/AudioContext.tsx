import React, { createContext, useContext, useEffect, useRef, useState, ReactNode } from 'react';
import { useAppState } from './AppStateContext';
import { useWebSocket } from './WebSocketContext';

interface AudioContextType {
  startListening: () => Promise<void>;
  stopListening: () => void;
  playAudio: (audioData: ArrayBuffer | string) => Promise<void>;
  stopAudio: () => void;
  isRecording: boolean;
  audioLevel: number;
}

const AudioContext = createContext<AudioContextType | undefined>(undefined);

export const useAudio = () => {
  const context = useContext(AudioContext);
  if (!context) {
    throw new Error('useAudio must be used within AudioProvider');
  }
  return context;
};

interface AudioProviderProps {
  children: ReactNode;
}

export const AudioProvider: React.FC<AudioProviderProps> = ({ children }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const { volume, isMuted, setListening } = useAppState();
  const { sendMessage, onMessage } = useWebSocket();
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const audioElementRef = useRef<HTMLAudioElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // Initialize audio context
  useEffect(() => {
    audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
    audioElementRef.current = new Audio();
    audioElementRef.current.volume = volume;

    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, []);

  // Update volume
  useEffect(() => {
    if (audioElementRef.current) {
      audioElementRef.current.volume = isMuted ? 0 : volume;
    }
  }, [volume, isMuted]);

  // Handle audio responses from server
  useEffect(() => {
    const unsubscribe = onMessage('audio_response', async (data) => {
      if (data.audio) {
        await playAudio(data.audio);
      }
    });
    return unsubscribe;
  }, []);

  const startListening = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        } 
      });
      
      streamRef.current = stream;
      setIsRecording(true);
      setListening(true);

      // Set up audio level monitoring
      if (audioContextRef.current) {
        const source = audioContextRef.current.createMediaStreamSource(stream);
        analyserRef.current = audioContextRef.current.createAnalyser();
        analyserRef.current.fftSize = 256;
        source.connect(analyserRef.current);

        // Monitor audio levels
        const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
        const checkLevel = () => {
          if (!isRecording) return;
          
          analyserRef.current!.getByteFrequencyData(dataArray);
          const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
          setAudioLevel(average / 255);
          
          requestAnimationFrame(checkLevel);
        };
        checkLevel();
      }

      // Set up media recorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      mediaRecorderRef.current = mediaRecorder;
      const chunks: Blob[] = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(chunks, { type: 'audio/webm' });
        const arrayBuffer = await audioBlob.arrayBuffer();
        const base64 = btoa(String.fromCharCode.apply(null, Array.from(new Uint8Array(arrayBuffer))));
        
        sendMessage({ 
          type: 'process_audio',
          audio: base64,
          mimeType: 'audio/webm'
        });
      };

      mediaRecorder.start(100); // Collect data every 100ms
    } catch (error) {
      console.error('Error starting recording:', error);
      setIsRecording(false);
      setListening(false);
    }
  };

  const stopListening = () => {
    setIsRecording(false);
    setListening(false);
    setAudioLevel(0);

    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
  };

  const playAudio = async (audioData: ArrayBuffer | string) => {
    try {
      if (!audioElementRef.current) return;

      let audioUrl: string;
      if (typeof audioData === 'string') {
        // Base64 encoded audio
        const binaryString = atob(audioData);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
          bytes[i] = binaryString.charCodeAt(i);
        }
        const blob = new Blob([bytes], { type: 'audio/wav' });
        audioUrl = URL.createObjectURL(blob);
      } else {
        // ArrayBuffer
        const blob = new Blob([audioData], { type: 'audio/wav' });
        audioUrl = URL.createObjectURL(blob);
      }

      audioElementRef.current.src = audioUrl;
      await audioElementRef.current.play();

      // Clean up URL after playback
      audioElementRef.current.onended = () => {
        URL.revokeObjectURL(audioUrl);
      };
    } catch (error) {
      console.error('Error playing audio:', error);
    }
  };

  const stopAudio = () => {
    if (audioElementRef.current) {
      audioElementRef.current.pause();
      audioElementRef.current.currentTime = 0;
    }
  };

  const contextValue: AudioContextType = {
    startListening,
    stopListening,
    playAudio,
    stopAudio,
    isRecording,
    audioLevel,
  };

  return (
    <AudioContext.Provider value={contextValue}>
      {children}
    </AudioContext.Provider>
  );
};