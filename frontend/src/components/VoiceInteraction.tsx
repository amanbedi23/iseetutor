import React, { useEffect, useState, useRef } from 'react';
import styled from '@emotion/styled';
import { motion, AnimatePresence } from 'framer-motion';
import { useAppState } from '../contexts/AppStateContext';
import { useWebSocket } from '../contexts/WebSocketContext';
import { useAudio } from '../contexts/AudioContext';
import VoiceVisualizer from './VoiceVisualizer';

const Container = styled(motion.div)`
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
`;

const BackButton = styled(motion.button)`
  position: absolute;
  top: 2rem;
  left: 2rem;
  background: rgba(255, 255, 255, 0.2);
  border: none;
  border-radius: 50%;
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  backdrop-filter: blur(10px);
  
  &:hover {
    background: rgba(255, 255, 255, 0.3);
  }
`;

const ModeSelector = styled(motion.div)`
  position: absolute;
  top: 2rem;
  right: 2rem;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  padding: 0.5rem;
  border-radius: 30px;
  display: flex;
  gap: 0.5rem;
`;

const ModeButton = styled(motion.button)<{ isActive: boolean }>`
  background: ${props => props.isActive 
    ? 'rgba(255, 255, 255, 0.4)' 
    : 'transparent'};
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  color: white;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.3rem;
  transition: all 0.2s ease;
  
  &:hover {
    background: rgba(255, 255, 255, 0.3);
  }
`;

const ConnectionStatus = styled(motion.div)<{ connected: boolean }>`
  position: absolute;
  top: 2rem;
  left: 50%;
  transform: translateX(-50%);
  background: ${props => props.connected 
    ? 'rgba(72, 187, 120, 0.2)' 
    : 'rgba(245, 101, 101, 0.2)'};
  backdrop-filter: blur(10px);
  padding: 0.5rem 1rem;
  border-radius: 20px;
  color: white;
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const VoiceButton = styled(motion.button)<{ isActive: boolean }>`
  width: 200px;
  height: 200px;
  border-radius: 50%;
  border: none;
  background: ${props => props.isActive 
    ? 'rgba(255, 255, 255, 0.95)' 
    : 'rgba(255, 255, 255, 0.3)'};
  backdrop-filter: blur(10px);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 4rem;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  transition: all 0.3s ease;
  position: relative;
  z-index: 2;
  
  &:hover {
    transform: scale(1.05);
  }
  
  &:active {
    transform: scale(0.95);
  }
`;

const StatusText = styled(motion.div)`
  margin-top: 2rem;
  font-size: 1.5rem;
  color: white;
  text-align: center;
  font-weight: 500;
`;

const TranscriptBox = styled(motion.div)`
  position: absolute;
  bottom: 2rem;
  left: 2rem;
  right: 2rem;
  max-height: 300px;
  background: rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
  border-radius: 15px;
  padding: 1.5rem;
  overflow-y: auto;
  color: white;
`;

const Message = styled.div<{ isUser: boolean }>`
  margin-bottom: 1rem;
  text-align: ${props => props.isUser ? 'right' : 'left'};
  
  & > div {
    display: inline-block;
    padding: 0.8rem 1.2rem;
    border-radius: 15px;
    background: ${props => props.isUser 
      ? 'rgba(255, 255, 255, 0.2)' 
      : 'rgba(255, 255, 255, 0.1)'};
    max-width: 70%;
  }
`;

const VisualizerContainer = styled(motion.div)`
  position: absolute;
  z-index: 0;
`;

const TextInput = styled.input`
  position: absolute;
  bottom: 2rem;
  left: 50%;
  transform: translateX(-50%);
  width: 90%;
  max-width: 600px;
  padding: 1rem 1.5rem;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 30px;
  color: white;
  font-size: 1rem;
  
  &::placeholder {
    color: rgba(255, 255, 255, 0.6);
  }
  
  &:focus {
    outline: none;
    border-color: rgba(255, 255, 255, 0.4);
    background: rgba(255, 255, 255, 0.15);
  }
`;

interface ChatMessage {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
}

interface VoiceInteractionProps {
  onNavigate: (view: 'home' | 'voice' | 'learning' | 'parent') => void;
}

const VoiceInteraction: React.FC<VoiceInteractionProps> = ({ onNavigate }) => {
  const { mode, setMode, isListening, isSpeaking, isThinking } = useAppState();
  const { connected, sendMessage, onMessage, startVoicePipeline, stopVoicePipeline } = useWebSocket();
  const { startListening, stopListening, audioLevel: audioLevelFromContext } = useAudio();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [currentTranscript, setCurrentTranscript] = useState('');
  const [voicePipelineActive, setVoicePipelineActive] = useState(false);
  const [textInput, setTextInput] = useState('');
  const [showTextInput, setShowTextInput] = useState(false);
  const [isAudioStreaming, setIsAudioStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Start voice pipeline when component mounts
    if (connected) {
      startVoicePipeline();
      setVoicePipelineActive(true);
      // Automatically show text input in cloud deployment
      setShowTextInput(true);
    }

    // Listen for voice pipeline events
    const unsubscribeStarted = onMessage('voice_started', (data) => {
      console.log('Voice pipeline started:', data);
      setVoicePipelineActive(true);
    });

    const unsubscribeStopped = onMessage('voice_stopped', (data) => {
      console.log('Voice pipeline stopped:', data);
      setVoicePipelineActive(false);
    });

    const unsubscribeTranscript = onMessage('voice_transcript', (data) => {
      setCurrentTranscript(data.text);
      // Add user message when transcript is final
      const newMessage: ChatMessage = {
        id: Date.now().toString(),
        text: data.text,
        isUser: true,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, newMessage]);
      setCurrentTranscript('');
    });

    const unsubscribeResponse = onMessage('voice_response', (data) => {
      const newMessage: ChatMessage = {
        id: Date.now().toString(),
        text: data.text,
        isUser: false,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, newMessage]);
    });

    const unsubscribeTextResponse = onMessage('text_response', (data) => {
      const newMessage: ChatMessage = {
        id: Date.now().toString(),
        text: data.text,
        isUser: false,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, newMessage]);
    });

    const unsubscribeError = onMessage('error', (data) => {
      console.error('Voice pipeline error:', data.message);
      // Show text input if voice is not available
      if (data.message && data.message.includes('Voice input is not available')) {
        setShowTextInput(true);
      }
    });

    const unsubscribeVoiceState = onMessage('voice_state', (data) => {
      console.log('Voice state:', data);
      // If voice is not available, show text input
      if (data.state === 'text_only') {
        setShowTextInput(true);
      }
    });

    return () => {
      unsubscribeStarted();
      unsubscribeStopped();
      unsubscribeTranscript();
      unsubscribeResponse();
      unsubscribeTextResponse();
      unsubscribeError();
      unsubscribeVoiceState();
      
      // Stop voice pipeline when leaving
      if (voicePipelineActive) {
        stopVoicePipeline();
      }
    };
  }, [connected]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    // Auto-scroll to latest message
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleModeChange = (newMode: 'tutor' | 'friend' | 'hybrid') => {
    setMode(newMode);
    sendMessage({
      type: 'voice_mode',
      mode: newMode
    });
  };

  const handleTextSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (textInput.trim() && connected) {
      // Add user message
      const userMessage: ChatMessage = {
        id: Date.now().toString(),
        text: textInput,
        isUser: true,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, userMessage]);

      // Send to backend with current mode
      sendMessage({
        type: 'text_input',
        text: textInput,
        mode: mode,
        user_context: { age: 12, grade: 7 }  // This would come from user profile
      });

      setTextInput('');
    }
  };

  const getStatusText = () => {
    if (!connected) return 'Disconnected';
    if (!voicePipelineActive) return 'Starting...';
    if (showTextInput) return 'Type your message below';
    if (isAudioStreaming && isListening) return 'Listening... (Tap to stop)';
    if (isAudioStreaming && !isListening) return 'Waiting for "Hey Jarvis"...';
    if (isListening) return 'Listening...';
    if (isThinking) return 'Thinking...';
    if (isSpeaking) return 'Speaking...';
    return 'Voice not available - Use text input below';
  };

  const getModeIcon = (modeType: string) => {
    switch (modeType) {
      case 'tutor': return '📚';
      case 'friend': return '🤗';
      case 'hybrid': return '✨';
      default: return '🤖';
    }
  };

  return (
    <Container
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <BackButton
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={() => onNavigate('home')}
      >
        ←
      </BackButton>

      <ConnectionStatus connected={connected}>
        <div style={{ 
          width: 8, 
          height: 8, 
          borderRadius: '50%', 
          background: connected ? '#48BB78' : '#F56565' 
        }} />
        {connected ? 'Connected' : 'Disconnected'}
      </ConnectionStatus>

      <ModeSelector>
        <ModeButton
          isActive={mode === 'tutor'}
          onClick={() => handleModeChange('tutor')}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          {getModeIcon('tutor')} Tutor
        </ModeButton>
        <ModeButton
          isActive={mode === 'friend'}
          onClick={() => handleModeChange('friend')}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          {getModeIcon('friend')} Friend
        </ModeButton>
        <ModeButton
          isActive={mode === 'hybrid'}
          onClick={() => handleModeChange('hybrid')}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          {getModeIcon('hybrid')} Hybrid
        </ModeButton>
      </ModeSelector>

      <AnimatePresence>
        {(isListening || isThinking || isSpeaking) && (
          <VisualizerContainer
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{ duration: 0.3 }}
          >
            <VoiceVisualizer 
              isActive={isListening || isSpeaking}
              audioLevel={isAudioStreaming ? audioLevelFromContext : (isListening ? 0.6 : isSpeaking ? 0.4 : 0.2)}
            />
          </VisualizerContainer>
        )}
      </AnimatePresence>

      <VoiceButton
        isActive={isListening}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={async () => {
          if (!isAudioStreaming) {
            // Start audio streaming from browser
            try {
              await startListening();
              setIsAudioStreaming(true);
              // Send manual trigger to voice pipeline
              sendMessage({ type: 'voice_trigger', source: 'button' });
            } catch (error) {
              console.error('Failed to start listening:', error);
            }
          } else {
            // Stop audio streaming
            stopListening();
            setIsAudioStreaming(false);
          }
        }}
        onDoubleClick={() => setShowTextInput(!showTextInput)}
        animate={{
          scale: isListening ? [1, 1.1, 1] : 1,
        }}
        transition={{
          repeat: isListening ? Infinity : 0,
          duration: 2,
        }}
      >
        {isListening ? '🎤' : '🎙️'}
      </VoiceButton>

      <StatusText
        animate={{
          opacity: isThinking || isSpeaking ? [1, 0.7, 1] : 1,
        }}
        transition={{
          repeat: isThinking || isSpeaking ? Infinity : 0,
          duration: 2,
        }}
      >
        {getStatusText()}
      </StatusText>

      {!showTextInput && messages.length > 0 && (
        <TranscriptBox
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          {messages.map((message) => (
            <Message key={message.id} isUser={message.isUser}>
              <div>{message.text}</div>
            </Message>
          ))}
          {currentTranscript && (
            <Message isUser={true}>
              <div style={{ opacity: 0.7 }}>{currentTranscript}...</div>
            </Message>
          )}
          <div ref={messagesEndRef} />
        </TranscriptBox>
      )}

      {showTextInput && (
        <form onSubmit={handleTextSubmit}>
          <TextInput
            type="text"
            placeholder="Type a message..."
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            autoFocus
            disabled={!connected}
          />
        </form>
      )}
    </Container>
  );
};

export default VoiceInteraction;