import React from 'react';
import styled from '@emotion/styled';
import { motion } from 'framer-motion';
import { useAppState } from '../contexts/AppStateContext';

const Container = styled(motion.div)`
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
`;

const Title = styled(motion.h1)`
  font-size: 4rem;
  color: white;
  margin-bottom: 2rem;
  text-align: center;
  font-weight: 700;
  text-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
`;

const Subtitle = styled(motion.p)`
  font-size: 1.5rem;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 4rem;
  text-align: center;
`;

const ButtonGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
  width: 100%;
  max-width: 1000px;
`;

const ModeButton = styled(motion.button)`
  background: rgba(255, 255, 255, 0.95);
  border: none;
  border-radius: 20px;
  padding: 3rem 2rem;
  cursor: pointer;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-5px);
    box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15);
  }

  &:active {
    transform: translateY(-2px);
  }
`;

const IconWrapper = styled.div`
  font-size: 4rem;
  margin-bottom: 1rem;
`;

const ButtonTitle = styled.h2`
  font-size: 1.8rem;
  color: #2d3748;
  margin-bottom: 0.5rem;
`;

const ButtonDescription = styled.p`
  font-size: 1.1rem;
  color: #4a5568;
  line-height: 1.5;
`;

const StartButton = styled(motion.button)`
  margin-top: 3rem;
  padding: 1.5rem 4rem;
  font-size: 1.3rem;
  background: white;
  color: #667eea;
  border: none;
  border-radius: 50px;
  cursor: pointer;
  font-weight: 600;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  
  &:hover {
    transform: scale(1.05);
    box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15);
  }
`;

const ParentPortalButton = styled(motion.button)`
  margin-top: 1.5rem;
  padding: 1rem 2rem;
  font-size: 1.1rem;
  background: transparent;
  color: white;
  border: 2px solid rgba(255, 255, 255, 0.8);
  border-radius: 50px;
  cursor: pointer;
  font-weight: 600;
  
  &:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: white;
  }
`;

interface HomeScreenProps {
  onNavigate: (view: 'home' | 'voice' | 'learning' | 'parent' | 'chat') => void;
}

const HomeScreen: React.FC<HomeScreenProps> = ({ onNavigate }) => {
  const { mode, setMode, user } = useAppState();

  const handleModeSelect = (selectedMode: 'tutor' | 'friend' | 'hybrid') => {
    setMode(selectedMode);
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.2,
      },
    },
    exit: { opacity: 0, transition: { duration: 0.3 } },
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: { duration: 0.5, ease: 'easeOut' as const },
    },
  };

  return (
    <Container
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      exit="exit"
    >
      <Title variants={itemVariants} className="home-title">
        {user ? `Welcome back, ${user.name}!` : 'Welcome to ISEE Tutor'}
      </Title>
      <Subtitle variants={itemVariants} className="home-subtitle">
        Choose how you'd like to learn today
      </Subtitle>

      <ButtonGrid className="button-grid">
        <ModeButton
          className="mode-button"
          variants={itemVariants}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => handleModeSelect('tutor')}
          style={{
            border: mode === 'tutor' ? '3px solid #667eea' : 'none',
          }}
        >
          <IconWrapper>📚</IconWrapper>
          <ButtonTitle>Tutor Mode</ButtonTitle>
          <ButtonDescription>
            Focused ISEE test preparation with structured lessons and practice questions
          </ButtonDescription>
        </ModeButton>

        <ModeButton
          className="mode-button"
          variants={itemVariants}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => handleModeSelect('friend')}
          style={{
            border: mode === 'friend' ? '3px solid #667eea' : 'none',
          }}
        >
          <IconWrapper>🤗</IconWrapper>
          <ButtonTitle>Friend Mode</ButtonTitle>
          <ButtonDescription>
            Fun learning through conversation, stories, and exploration
          </ButtonDescription>
        </ModeButton>

        <ModeButton
          className="mode-button"
          variants={itemVariants}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => handleModeSelect('hybrid')}
          style={{
            border: mode === 'hybrid' ? '3px solid #667eea' : 'none',
          }}
        >
          <IconWrapper>✨</IconWrapper>
          <ButtonTitle>Smart Mode</ButtonTitle>
          <ButtonDescription>
            Adapts between tutoring and friendly chat based on your needs
          </ButtonDescription>
        </ModeButton>
      </ButtonGrid>

      <StartButton
        variants={itemVariants}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => onNavigate('voice')}
      >
        Start Voice Learning
      </StartButton>

      <StartButton
        variants={itemVariants}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => onNavigate('chat')}
        style={{ marginTop: '1rem', background: '#764ba2', color: 'white' }}
      >
        💬 Text Chat
      </StartButton>

      <ParentPortalButton
        variants={itemVariants}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={() => onNavigate('parent')}
      >
        👨‍👩‍👧‍👦 Parent Portal
      </ParentPortalButton>
    </Container>
  );
};

export default HomeScreen;