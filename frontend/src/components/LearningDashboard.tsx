import React from 'react';
import styled from '@emotion/styled';
import { motion } from 'framer-motion';
import { useAppState } from '../contexts/AppStateContext';

const Container = styled(motion.div)`
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f7fafc;
  overflow: hidden;
`;

const Header = styled.div`
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 2rem;
  color: white;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
`;

const HeaderContent = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const Title = styled.h1`
  font-size: 2rem;
  font-weight: 700;
`;

const BackButton = styled(motion.button)`
  background: rgba(255, 255, 255, 0.2);
  border: none;
  border-radius: 30px;
  padding: 0.8rem 1.5rem;
  color: white;
  cursor: pointer;
  backdrop-filter: blur(10px);
  font-weight: 600;
  
  &:hover {
    background: rgba(255, 255, 255, 0.3);
  }
`;

const Content = styled.div`
  flex: 1;
  padding: 2rem;
  overflow-y: auto;
`;

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 3rem;
`;

const StatCard = styled(motion.div)`
  background: white;
  border-radius: 15px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  
  &:hover {
    box-shadow: 0 8px 15px rgba(0, 0, 0, 0.1);
  }
`;

const StatIcon = styled.div`
  font-size: 2.5rem;
  margin-bottom: 1rem;
`;

const StatValue = styled.div`
  font-size: 2rem;
  font-weight: 700;
  color: #2d3748;
  margin-bottom: 0.5rem;
`;

const StatLabel = styled.div`
  color: #718096;
  font-size: 1rem;
`;

const ProgressSection = styled.div`
  background: white;
  border-radius: 15px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  margin-bottom: 2rem;
`;

const SectionTitle = styled.h2`
  font-size: 1.5rem;
  color: #2d3748;
  margin-bottom: 1.5rem;
  font-weight: 600;
`;

const TopicList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1rem;
`;

const TopicItem = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  background: #f7fafc;
  border-radius: 10px;
`;

const TopicName = styled.div`
  font-weight: 500;
  color: #4a5568;
`;

const ProgressBar = styled.div`
  width: 200px;
  height: 8px;
  background: #e2e8f0;
  border-radius: 4px;
  overflow: hidden;
`;

const ProgressFill = styled(motion.div)<{ progress: number }>`
  height: 100%;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  width: ${props => props.progress}%;
`;

interface LearningDashboardProps {
  onNavigate: (view: 'home' | 'voice' | 'learning') => void;
}

const LearningDashboard: React.FC<LearningDashboardProps> = ({ onNavigate }) => {
  const { user } = useAppState();

  // Demo data - in real app, this would come from the API
  const stats = {
    questionsAnswered: user?.progress.questionsAnswered || 0,
    correctAnswers: user?.progress.correctAnswers || 0,
    studyStreak: 5,
    totalTime: '2h 35m',
  };

  const topics = [
    { name: 'Vocabulary', progress: 75 },
    { name: 'Mathematics', progress: 60 },
    { name: 'Reading Comprehension', progress: 85 },
    { name: 'Quantitative Reasoning', progress: 40 },
    { name: 'Verbal Reasoning', progress: 55 },
  ];

  const accuracy = stats.questionsAnswered > 0 
    ? Math.round((stats.correctAnswers / stats.questionsAnswered) * 100)
    : 0;

  return (
    <Container
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <Header>
        <HeaderContent>
          <Title>Learning Progress</Title>
          <BackButton
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => onNavigate('home')}
          >
            Back to Home
          </BackButton>
        </HeaderContent>
      </Header>

      <Content>
        <StatsGrid>
          <StatCard whileHover={{ y: -5 }}>
            <StatIcon>❓</StatIcon>
            <StatValue>{stats.questionsAnswered}</StatValue>
            <StatLabel>Questions Answered</StatLabel>
          </StatCard>

          <StatCard whileHover={{ y: -5 }}>
            <StatIcon>✅</StatIcon>
            <StatValue>{accuracy}%</StatValue>
            <StatLabel>Accuracy Rate</StatLabel>
          </StatCard>

          <StatCard whileHover={{ y: -5 }}>
            <StatIcon>🔥</StatIcon>
            <StatValue>{stats.studyStreak}</StatValue>
            <StatLabel>Day Streak</StatLabel>
          </StatCard>

          <StatCard whileHover={{ y: -5 }}>
            <StatIcon>⏱️</StatIcon>
            <StatValue>{stats.totalTime}</StatValue>
            <StatLabel>Study Time</StatLabel>
          </StatCard>
        </StatsGrid>

        <ProgressSection>
          <SectionTitle>Topic Progress</SectionTitle>
          <TopicList>
            {topics.map((topic, index) => (
              <TopicItem key={index}>
                <TopicName>{topic.name}</TopicName>
                <ProgressBar>
                  <ProgressFill
                    progress={topic.progress}
                    initial={{ width: 0 }}
                    animate={{ width: `${topic.progress}%` }}
                    transition={{ delay: index * 0.1, duration: 0.5 }}
                  />
                </ProgressBar>
              </TopicItem>
            ))}
          </TopicList>
        </ProgressSection>
      </Content>
    </Container>
  );
};

export default LearningDashboard;