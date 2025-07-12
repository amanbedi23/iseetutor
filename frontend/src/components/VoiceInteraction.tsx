import React, { useEffect, useState } from 'react';
import styled from '@emotion/styled';
import { motion, AnimatePresence } from 'framer-motion';
import { useAppState } from '../contexts/AppStateContext';
import { useAudio } from '../contexts/AudioContext';
import { useWebSocket } from '../contexts/WebSocketContext';

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

const ModeIndicator = styled(motion.div)`
  position: absolute;
  top: 2rem;
  right: 2rem;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  padding: 1rem 2rem;
  border-radius: 30px;
  color: white;
  font-weight: 600;
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
  max-height: 200px;
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

const AudioLevelIndicator = styled(motion.div)<{ level: number }>`
  position: absolute;
  width: 250px;
  height: 250px;
  border-radius: 50%;
  border: 4px solid rgba(255, 255, 255, ${props => props.level});
  pointer-events: none;
`;

interface ChatMessage {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
}

interface VoiceInteractionProps {
  onNavigate: (view: 'home' | 'voice' | 'learning') => void;
}

const VoiceInteraction: React.FC<VoiceInteractionProps> = ({ onNavigate }) => {
  const { mode, isListening, isSpeaking, isThinking } = useAppState();
  const { startListening, stopListening, isRecording, audioLevel } = useAudio();
  const { sendMessage, onMessage } = useWebSocket();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [currentTranscript, setCurrentTranscript] = useState('');

  useEffect(() => {
    // Listen for transcription updates
    const unsubscribeTranscript = onMessage('transcript', (data) => {
      setCurrentTranscript(data.text);
    });

    // Listen for responses
    const unsubscribeResponse = onMessage('response', (data) => {
      const newMessage: ChatMessage = {
        id: Date.now().toString(),
        text: data.text,
        isUser: false,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, newMessage]);
      setCurrentTranscript('');
    });

    return () => {
      unsubscribeTranscript();
      unsubscribeResponse();
    };
  }, [onMessage]);

  const handleVoiceButtonClick = async () => {
    if (isRecording) {
      stopListening();
      
      // Add user message
      if (currentTranscript) {
        const newMessage: ChatMessage = {
          id: Date.now().toString(),
          text: currentTranscript,
          isUser: true,
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, newMessage]);
      }
    } else {
      await startListening();
    }
  };

  const getStatusText = () => {
    if (isRecording) return 'Listening...';
    if (isThinking) return 'Thinking...';
    if (isSpeaking) return 'Speaking...';
    return 'Tap to speak';
  };

  const getModeIcon = () => {
    switch (mode) {
      case 'tutor': return '📚';
      case 'friend': return '🤗';
      case 'hybrid': return '✨';
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

      <ModeIndicator>
        <span>{getModeIcon()}</span>
        <span>{mode.charAt(0).toUpperCase() + mode.slice(1)} Mode</span>
      </ModeIndicator>

      <AnimatePresence>
        {isRecording && (
          <AudioLevelIndicator
            level={audioLevel}
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.8, opacity: 0 }}
          />
        )}
      </AnimatePresence>

      <VoiceButton
        isActive={isRecording}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={handleVoiceButtonClick}
        animate={{
          scale: isRecording ? [1, 1.1, 1] : 1,
        }}
        transition={{
          repeat: isRecording ? Infinity : 0,
          duration: 2,
        }}
      >
        {isRecording ? '🎤' : '🎙️'}
      </VoiceButton>

      <StatusText
        animate={{
          opacity: [1, 0.7, 1],
        }}
        transition={{
          repeat: Infinity,
          duration: 2,
        }}
      >
        {getStatusText()}
      </StatusText>

      <TranscriptBox>
        {messages.map((message) => (
          <Message key={message.id} isUser={message.isUser}>
            <div>{message.text}</div>
          </Message>
        ))}
        {currentTranscript && (
          <Message isUser={true}>
            <div style={{ opacity: 0.7 }}>{currentTranscript}</div>
          </Message>
        )}
      </TranscriptBox>
    </Container>
  );
};

export default VoiceInteraction;