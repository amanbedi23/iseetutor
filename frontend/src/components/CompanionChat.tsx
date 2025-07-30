import React, { useState, useRef, useEffect } from 'react';
import styled from '@emotion/styled';
import { motion, AnimatePresence } from 'framer-motion';

const Container = styled.div`
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
`;

const Header = styled.div`
  padding: 1.5rem;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  position: relative;
`;

const BackButton = styled.button`
  position: absolute;
  left: 1rem;
  top: 50%;
  transform: translateY(-50%);
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(255, 255, 255, 0.3);
  }
`;

const Title = styled.h2`
  color: white;
  margin: 0;
  font-size: 1.5rem;
  text-align: center;
`;

const ModeSelector = styled.div`
  display: flex;
  gap: 0.5rem;
  justify-content: center;
  margin-top: 1rem;
`;

const ModeButton = styled.button<{ active: boolean }>`
  background: ${props => props.active ? 'rgba(255, 255, 255, 0.3)' : 'rgba(255, 255, 255, 0.1)'};
  border: none;
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 0.9rem;
  
  &:hover {
    background: rgba(255, 255, 255, 0.3);
  }
`;

const ChatContainer = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
`;

const MessageWrapper = styled(motion.div)<{ isUser: boolean }>`
  display: flex;
  justify-content: ${props => props.isUser ? 'flex-end' : 'flex-start'};
`;

const Message = styled.div<{ isUser: boolean }>`
  background: ${props => props.isUser ? 'rgba(255, 255, 255, 0.9)' : 'rgba(255, 255, 255, 0.2)'};
  color: ${props => props.isUser ? '#333' : 'white'};
  padding: 1rem;
  border-radius: 20px;
  max-width: 70%;
  word-wrap: break-word;
  backdrop-filter: blur(10px);
`;

const InputContainer = styled.form`
  display: flex;
  gap: 1rem;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-top: 1px solid rgba(255, 255, 255, 0.2);
`;

const Input = styled.input`
  flex: 1;
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  padding: 1rem;
  border-radius: 25px;
  font-size: 1rem;
  outline: none;
  
  &::placeholder {
    color: rgba(255, 255, 255, 0.7);
  }
`;

const SendButton = styled.button`
  background: rgba(255, 255, 255, 0.3);
  border: none;
  color: white;
  width: 50px;
  height: 50px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(255, 255, 255, 0.4);
    transform: scale(1.1);
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const LoadingDots = styled.div`
  display: flex;
  gap: 0.3rem;
  padding: 0.5rem 0;
  
  span {
    width: 8px;
    height: 8px;
    background: white;
    border-radius: 50%;
    animation: bounce 1.4s infinite ease-in-out both;
    
    &:nth-of-type(1) {
      animation-delay: -0.32s;
    }
    
    &:nth-of-type(2) {
      animation-delay: -0.16s;
    }
  }
  
  @keyframes bounce {
    0%, 80%, 100% {
      transform: scale(0);
    }
    40% {
      transform: scale(1);
    }
  }
`;

interface ChatMessage {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
}

interface CompanionChatProps {
  initialMode?: 'tutor' | 'friend' | 'hybrid';
  onNavigate?: (view: string) => void;
}

const CompanionChat: React.FC<CompanionChatProps> = ({ initialMode = 'hybrid', onNavigate }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [mode, setMode] = useState<'tutor' | 'friend' | 'hybrid'>(initialMode);
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Scroll to bottom when messages change
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    // Add welcome message based on mode
    const welcomeMessages = {
      tutor: "Hello! I'm your ISEE tutor. I can help you with verbal reasoning, math, reading comprehension, and essay writing. What would you like to work on today?",
      friend: "Hi there! I'm your AI friend. We can chat about anything you'd like - your hobbies, school, or just have fun conversations. What's on your mind?",
      hybrid: "Hey! I'm here to help with your studies or just chat. We can work on ISEE prep or talk about anything else you're interested in. What would you like to do?"
    };

    setMessages([{
      id: 'welcome',
      text: welcomeMessages[mode],
      isUser: false,
      timestamp: new Date()
    }]);
  }, [mode]);

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      text: input,
      isUser: true,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await fetch('/api/companion/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: input,
          mode: mode,
          user_context: {
            age: 12, // This would come from user profile
            grade: 7  // This would come from user profile
          }
        })
      });

      const data = await response.json();

      if (response.ok) {
        const aiMessage: ChatMessage = {
          id: Date.now().toString(),
          text: data.response,
          isUser: false,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, aiMessage]);
      } else {
        throw new Error(data.detail || 'Failed to get response');
      }
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage: ChatMessage = {
        id: Date.now().toString(),
        text: "I'm having trouble connecting right now. Please try again in a moment.",
        isUser: false,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container>
      <Header>
        {onNavigate && (
          <BackButton onClick={() => onNavigate('home')}>
            ←
          </BackButton>
        )}
        <Title>ISEE Tutor Companion</Title>
        <ModeSelector>
          <ModeButton 
            active={mode === 'tutor'} 
            onClick={() => setMode('tutor')}
          >
            📚 Tutor
          </ModeButton>
          <ModeButton 
            active={mode === 'friend'} 
            onClick={() => setMode('friend')}
          >
            🤝 Friend
          </ModeButton>
          <ModeButton 
            active={mode === 'hybrid'} 
            onClick={() => setMode('hybrid')}
          >
            🎯 Hybrid
          </ModeButton>
        </ModeSelector>
      </Header>

      <ChatContainer>
        <AnimatePresence>
          {messages.map((message) => (
            <MessageWrapper
              key={message.id}
              isUser={message.isUser}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              <Message isUser={message.isUser}>
                {message.text}
              </Message>
            </MessageWrapper>
          ))}
          {loading && (
            <MessageWrapper
              isUser={false}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <Message isUser={false}>
                <LoadingDots>
                  <span />
                  <span />
                  <span />
                </LoadingDots>
              </Message>
            </MessageWrapper>
          )}
        </AnimatePresence>
        <div ref={chatEndRef} />
      </ChatContainer>

      <InputContainer onSubmit={sendMessage}>
        <Input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          disabled={loading}
        />
        <SendButton type="submit" disabled={!input.trim() || loading}>
          →
        </SendButton>
      </InputContainer>
    </Container>
  );
};

export default CompanionChat;