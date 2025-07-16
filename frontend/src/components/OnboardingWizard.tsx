import React, { useState } from 'react';
import styled from '@emotion/styled';
import { motion, AnimatePresence } from 'framer-motion';

const OnboardingContainer = styled.div`
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 2rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
`;

const WizardCard = styled.div`
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  padding: 3rem;
  max-width: 800px;
  width: 100%;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
`;

const StepperContainer = styled.div`
  display: flex;
  justify-content: center;
  margin-bottom: 3rem;
  position: relative;
`;

const Step = styled.div<{ active: boolean; completed: boolean }>`
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: ${props => props.completed ? '#4CAF50' : props.active ? '#667eea' : '#e0e0e0'};
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  position: relative;
  z-index: 1;
  transition: all 0.3s ease;
  
  &:not(:last-child) {
    margin-right: 80px;
    
    &::after {
      content: '';
      position: absolute;
      width: 80px;
      height: 2px;
      background: ${props => props.completed ? '#4CAF50' : '#e0e0e0'};
      left: 100%;
      top: 50%;
      transform: translateY(-50%);
      z-index: 0;
    }
  }
`;

const StepLabel = styled.div`
  position: absolute;
  top: 100%;
  margin-top: 0.5rem;
  white-space: nowrap;
  font-size: 0.875rem;
  color: #666;
`;

const ContentArea = styled.div`
  min-height: 400px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
`;

const Title = styled.h1`
  color: #333;
  margin-bottom: 1rem;
  text-align: center;
`;

const Subtitle = styled.p`
  color: #666;
  font-size: 1.25rem;
  text-align: center;
  margin-bottom: 2rem;
`;

const FormGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  width: 100%;
  margin-top: 2rem;
`;

const InputField = styled.input`
  width: 100%;
  padding: 1rem;
  border: 2px solid #e0e0e0;
  border-radius: 10px;
  font-size: 1.1rem;
  transition: border-color 0.3s ease;
  
  &:focus {
    outline: none;
    border-color: #667eea;
  }
`;

const SelectField = styled.select`
  width: 100%;
  padding: 1rem;
  border: 2px solid #e0e0e0;
  border-radius: 10px;
  font-size: 1.1rem;
  background: white;
  cursor: pointer;
  
  &:focus {
    outline: none;
    border-color: #667eea;
  }
`;

const Label = styled.label`
  display: block;
  margin-bottom: 0.5rem;
  color: #555;
  font-weight: 500;
`;

const AvatarGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 1rem;
  margin-top: 1rem;
`;

const AvatarOption = styled(motion.div)<{ selected: boolean }>`
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: ${props => props.selected ? props.color : '#f0f0f0'};
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2.5rem;
  cursor: pointer;
  border: ${props => props.selected ? '4px solid #667eea' : '4px solid transparent'};
  transition: all 0.2s ease;
`;

const SliderContainer = styled.div`
  width: 100%;
  max-width: 400px;
  margin: 2rem auto;
`;

const Slider = styled.input`
  width: 100%;
  -webkit-appearance: none;
  height: 8px;
  border-radius: 5px;
  background: #e0e0e0;
  outline: none;
  
  &::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 25px;
    height: 25px;
    border-radius: 50%;
    background: #667eea;
    cursor: pointer;
  }
`;

const SliderLabels = styled.div`
  display: flex;
  justify-content: space-between;
  margin-top: 0.5rem;
  color: #666;
`;

const Button = styled(motion.button)`
  padding: 1rem 2rem;
  border: none;
  border-radius: 10px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const PrimaryButton = styled(Button)`
  background: #667eea;
  color: white;
  
  &:hover:not(:disabled) {
    background: #5a67d8;
    transform: translateY(-2px);
  }
`;

const SecondaryButton = styled(Button)`
  background: transparent;
  color: #667eea;
  border: 2px solid #667eea;
  
  &:hover:not(:disabled) {
    background: #667eea;
    color: white;
  }
`;

const NavigationButtons = styled.div`
  display: flex;
  justify-content: space-between;
  margin-top: 3rem;
`;

const MicButton = styled(motion.button)<{ recording?: boolean }>`
  width: 120px;
  height: 120px;
  border-radius: 50%;
  border: none;
  background: ${props => props.recording ? '#e74c3c' : '#667eea'};
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 3rem;
  cursor: pointer;
  margin: 2rem auto;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  transition: all 0.3s ease;
  
  &:hover {
    transform: scale(1.05);
  }
`;

const CheckIcon = styled.div`
  color: #4CAF50;
  font-size: 4rem;
  margin: 2rem auto;
`;

const FeatureList = styled.ul`
  list-style: none;
  padding: 0;
  margin: 2rem 0;
`;

const FeatureItem = styled.li`
  display: flex;
  align-items: center;
  margin-bottom: 1rem;
  font-size: 1.1rem;
  color: #555;
  
  &::before {
    content: '✓';
    color: #4CAF50;
    font-weight: bold;
    margin-right: 1rem;
    font-size: 1.5rem;
  }
`;

const steps = ['Welcome', 'Create Profile', 'Voice Setup', 'Ready to Learn'];

const avatarOptions = [
  { id: 'astronaut', emoji: '👨‍🚀', color: '#3498db' },
  { id: 'scientist', emoji: '👩‍🔬', color: '#9b59b6' },
  { id: 'artist', emoji: '👨‍🎨', color: '#e74c3c' },
  { id: 'teacher', emoji: '👩‍🏫', color: '#2ecc71' },
  { id: 'athlete', emoji: '🏃‍♂️', color: '#f39c12' },
  { id: 'musician', emoji: '🎸', color: '#1abc9c' },
];

interface OnboardingWizardProps {
  onComplete?: () => void;
}

export const OnboardingWizard: React.FC<OnboardingWizardProps> = ({ onComplete }) => {
  const [activeStep, setActiveStep] = useState(0);
  const [studentName, setStudentName] = useState('');
  const [age, setAge] = useState<number | ''>('');
  const [grade, setGrade] = useState<number | ''>('');
  const [selectedAvatar, setSelectedAvatar] = useState(avatarOptions[0]);
  const [voiceSpeed, setVoiceSpeed] = useState(1.0);
  const [isRecording, setIsRecording] = useState(false);
  const [voiceTestComplete, setVoiceTestComplete] = useState(false);

  const handleNext = () => {
    if (activeStep === steps.length - 1) {
      // Save profile and complete onboarding
      saveProfile();
      if (onComplete) {
        onComplete();
      }
    } else {
      setActiveStep((prev) => prev + 1);
    }
  };

  const handleBack = () => {
    setActiveStep((prev) => prev - 1);
  };

  const saveProfile = async () => {
    const profile = {
      name: studentName,
      age,
      grade,
      avatar: selectedAvatar,
      voice_speed: voiceSpeed,
      onboarding_complete: true,
    };

    try {
      await fetch('/api/users/profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(profile),
      });
    } catch (error) {
      console.error('Failed to save profile:', error);
    }
  };

  const startVoiceTest = () => {
    setIsRecording(true);
    // Simulate voice recording
    setTimeout(() => {
      setIsRecording(false);
      setVoiceTestComplete(true);
    }, 3000);
  };

  const playTestMessage = () => {
    // In real implementation, this would use TTS
    const utterance = new SpeechSynthesisUtterance(
      `Hi ${studentName}! I'm your learning companion. Let's have fun learning together!`
    );
    utterance.rate = voiceSpeed;
    window.speechSynthesis.speak(utterance);
  };

  const renderStepContent = () => {
    switch (activeStep) {
      case 0: // Welcome
        return (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <div style={{ textAlign: 'center' }}>
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: 'spring', stiffness: 200 }}
                style={{ fontSize: '5rem', marginBottom: '2rem' }}
              >
                🎓
              </motion.div>
              <Title>Welcome to ISEE Tutor!</Title>
              <Subtitle>
                I'm here to help you learn and grow. Let's set up your profile!
              </Subtitle>
              <FeatureList>
                <FeatureItem>Create your personal profile</FeatureItem>
                <FeatureItem>Set up your voice preferences</FeatureItem>
                <FeatureItem>Get ready to start learning</FeatureItem>
              </FeatureList>
            </div>
          </motion.div>
        );

      case 1: // Create Profile
        return (
          <motion.div
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
          >
            <Title>Let's Get to Know You!</Title>
            <FormGrid>
              <div>
                <Label>What's your name?</Label>
                <InputField
                  type="text"
                  value={studentName}
                  onChange={(e) => setStudentName(e.target.value)}
                  placeholder="Enter your name"
                />
              </div>
              <div>
                <Label>How old are you?</Label>
                <SelectField
                  value={age}
                  onChange={(e) => setAge(Number(e.target.value))}
                >
                  <option value="">Select age</option>
                  {[...Array(14)].map((_, i) => (
                    <option key={i + 5} value={i + 5}>
                      {i + 5} years old
                    </option>
                  ))}
                </SelectField>
              </div>
              <div>
                <Label>What grade are you in?</Label>
                <SelectField
                  value={grade}
                  onChange={(e) => setGrade(Number(e.target.value))}
                >
                  <option value="">Select grade</option>
                  {[...Array(12)].map((_, i) => (
                    <option key={i + 1} value={i + 1}>
                      Grade {i + 1}
                    </option>
                  ))}
                </SelectField>
              </div>
            </FormGrid>
            <div style={{ marginTop: '2rem' }}>
              <Label>Choose Your Avatar</Label>
              <AvatarGrid>
                {avatarOptions.map((avatar) => (
                  <AvatarOption
                    key={avatar.id}
                    color={avatar.color}
                    selected={selectedAvatar.id === avatar.id}
                    onClick={() => setSelectedAvatar(avatar)}
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    {avatar.emoji}
                  </AvatarOption>
                ))}
              </AvatarGrid>
            </div>
          </motion.div>
        );

      case 2: // Voice Setup
        return (
          <motion.div
            initial={{ opacity: 0, x: -50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
          >
            <Title>Voice Settings</Title>
            <Subtitle>Let's make sure I sound just right for you!</Subtitle>
            
            <SliderContainer>
              <Label>Voice Speed</Label>
              <Slider
                type="range"
                min="0.5"
                max="1.5"
                step="0.1"
                value={voiceSpeed}
                onChange={(e) => setVoiceSpeed(parseFloat(e.target.value))}
              />
              <SliderLabels>
                <span>Slow</span>
                <span>Normal</span>
                <span>Fast</span>
              </SliderLabels>
              <PrimaryButton
                onClick={playTestMessage}
                style={{ marginTop: '1rem', width: '100%' }}
              >
                🔊 Test Voice Speed
              </PrimaryButton>
            </SliderContainer>

            <div style={{ textAlign: 'center', marginTop: '3rem' }}>
              <Label>Say "Hey Tutor" to test wake word detection</Label>
              {isRecording ? (
                <motion.div
                  animate={{ scale: [1, 1.2, 1] }}
                  transition={{ repeat: Infinity, duration: 1 }}
                >
                  <MicButton recording>
                    🎤
                  </MicButton>
                  <p>Listening...</p>
                </motion.div>
              ) : voiceTestComplete ? (
                <div>
                  <CheckIcon>✓</CheckIcon>
                  <p style={{ color: '#4CAF50', fontSize: '1.2rem' }}>
                    Great! Voice detection is working perfectly!
                  </p>
                </div>
              ) : (
                <MicButton onClick={startVoiceTest}>
                  🎤
                </MicButton>
              )}
            </div>
          </motion.div>
        );

      case 3: // Ready to Learn
        return (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5 }}
          >
            <div style={{ textAlign: 'center' }}>
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: 'spring', stiffness: 200 }}
              >
                <AvatarOption
                  color={selectedAvatar.color}
                  selected={true}
                  style={{ 
                    width: '120px', 
                    height: '120px', 
                    margin: '0 auto 2rem',
                    fontSize: '4rem'
                  }}
                >
                  {selectedAvatar.emoji}
                </AvatarOption>
              </motion.div>
              <Title>All Set, {studentName}!</Title>
              <Subtitle>You're ready to start your learning journey!</Subtitle>
              <FeatureList>
                <FeatureItem>Ask me any question</FeatureItem>
                <FeatureItem>Practice for the ISEE test</FeatureItem>
                <FeatureItem>Play educational games</FeatureItem>
                <FeatureItem>Track your progress</FeatureItem>
              </FeatureList>
            </div>
          </motion.div>
        );

      default:
        return null;
    }
  };

  const canProceed = () => {
    switch (activeStep) {
      case 1:
        return studentName && age && grade;
      case 2:
        return voiceTestComplete;
      default:
        return true;
    }
  };

  return (
    <OnboardingContainer>
      <WizardCard>
        <StepperContainer>
          {steps.map((label, index) => (
            <Step
              key={label}
              active={index === activeStep}
              completed={index < activeStep}
            >
              {index < activeStep ? '✓' : index + 1}
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </StepperContainer>

        <ContentArea>
          <AnimatePresence mode="wait">
            {renderStepContent()}
          </AnimatePresence>
        </ContentArea>

        <NavigationButtons>
          <SecondaryButton
            onClick={handleBack}
            disabled={activeStep === 0}
            style={{ visibility: activeStep === 0 ? 'hidden' : 'visible' }}
          >
            ← Back
          </SecondaryButton>
          <PrimaryButton
            onClick={handleNext}
            disabled={!canProceed()}
          >
            {activeStep === steps.length - 1 ? 'Start Learning! 🚀' : 'Next →'}
          </PrimaryButton>
        </NavigationButtons>
      </WizardCard>
    </OnboardingContainer>
  );
};