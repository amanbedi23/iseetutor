import React, { useState } from 'react';
import styled from '@emotion/styled';
import { motion } from 'framer-motion';

const Container = styled(motion.div)`
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f7fafc;
  overflow: hidden;
`;

const Header = styled.div`
  background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
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

const ChildSelector = styled.div`
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  flex-wrap: wrap;
`;

const ChildCard = styled(motion.button)<{ active: boolean }>`
  padding: 1rem 2rem;
  border: 2px solid ${props => props.active ? '#667eea' : '#e2e8f0'};
  background: ${props => props.active ? '#667eea' : 'white'};
  color: ${props => props.active ? 'white' : '#4a5568'};
  border-radius: 15px;
  cursor: pointer;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
  }
`;

const DashboardGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
`;

const InfoCard = styled(motion.div)`
  background: white;
  border-radius: 15px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  
  &:hover {
    box-shadow: 0 8px 15px rgba(0, 0, 0, 0.1);
  }
`;

const CardTitle = styled.h3`
  font-size: 1.3rem;
  color: #2d3748;
  margin-bottom: 1.5rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const QuickStats = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1rem;
`;

const StatRow = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.8rem;
  background: #f7fafc;
  border-radius: 8px;
`;

const StatLabel = styled.div`
  color: #4a5568;
  font-size: 0.95rem;
`;

const StatValue = styled.div`
  color: #2d3748;
  font-weight: 600;
  font-size: 1.1rem;
`;

const RecentActivity = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1rem;
`;

const ActivityItem = styled.div`
  display: flex;
  gap: 1rem;
  padding: 1rem;
  background: #f7fafc;
  border-radius: 10px;
  align-items: center;
`;

const ActivityIcon = styled.div`
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
`;

const ActivityDetails = styled.div`
  flex: 1;
`;

const ActivityTitle = styled.div`
  font-weight: 600;
  color: #2d3748;
  margin-bottom: 0.25rem;
`;

const ActivityTime = styled.div`
  font-size: 0.85rem;
  color: #718096;
`;

const LearningGoals = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1rem;
`;

const GoalItem = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
`;

const GoalCheckbox = styled.div<{ checked: boolean }>`
  width: 24px;
  height: 24px;
  border: 2px solid ${props => props.checked ? '#48bb78' : '#cbd5e0'};
  background: ${props => props.checked ? '#48bb78' : 'transparent'};
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 0.8rem;
  transition: all 0.2s;
`;

const GoalText = styled.div<{ checked: boolean }>`
  color: #4a5568;
  text-decoration: ${props => props.checked ? 'line-through' : 'none'};
  opacity: ${props => props.checked ? 0.6 : 1};
`;

const ActionButtons = styled.div`
  display: flex;
  gap: 1rem;
  margin-top: 2rem;
  flex-wrap: wrap;
`;

const ActionButton = styled(motion.button)`
  padding: 1rem 2rem;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s;
`;

const PrimaryButton = styled(ActionButton)`
  background: #667eea;
  color: white;
  
  &:hover {
    background: #5a67d8;
  }
`;

const SecondaryButton = styled(ActionButton)`
  background: #e2e8f0;
  color: #4a5568;
  
  &:hover {
    background: #cbd5e0;
  }
`;

const AlertCard = styled(motion.div)`
  background: #fff5f5;
  border: 1px solid #feb2b2;
  border-radius: 10px;
  padding: 1rem;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 1rem;
`;

const AlertIcon = styled.div`
  color: #e53e3e;
  font-size: 1.5rem;
`;

const AlertText = styled.div`
  color: #742a2a;
  font-size: 0.95rem;
`;

interface Child {
  id: string;
  name: string;
  grade: number;
  avatar: string;
}

interface ParentDashboardProps {
  onNavigate: (view: 'home' | 'voice' | 'learning' | 'parent') => void;
}

const ParentDashboard: React.FC<ParentDashboardProps> = ({ onNavigate }) => {
  const [selectedChild, setSelectedChild] = useState<string>('child1');

  // Demo data
  const children: Child[] = [
    { id: 'child1', name: 'Emma', grade: 5, avatar: '👧' },
    { id: 'child2', name: 'Lucas', grade: 3, avatar: '👦' },
  ];

  const selectedChildData = children.find(c => c.id === selectedChild);

  const recentActivities = [
    { icon: '📚', title: 'Completed Math Quiz', time: '2 hours ago', type: 'quiz' },
    { icon: '🎯', title: 'Achieved 90% accuracy', time: '3 hours ago', type: 'achievement' },
    { icon: '📖', title: 'Read "The Solar System"', time: 'Yesterday', type: 'reading' },
    { icon: '✅', title: 'Finished vocabulary practice', time: 'Yesterday', type: 'practice' },
  ];

  const weeklyGoals = [
    { id: 1, text: 'Complete 5 math quizzes', checked: true },
    { id: 2, text: 'Read 3 science articles', checked: true },
    { id: 3, text: 'Practice vocabulary for 30 minutes', checked: false },
    { id: 4, text: 'Achieve 80% accuracy on all tests', checked: false },
  ];

  return (
    <Container
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <Header>
        <HeaderContent>
          <Title>Parent Dashboard</Title>
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
        <ChildSelector>
          {children.map(child => (
            <ChildCard
              key={child.id}
              active={selectedChild === child.id}
              onClick={() => setSelectedChild(child.id)}
              whileHover={{ y: -2 }}
              whileTap={{ scale: 0.98 }}
            >
              <span style={{ fontSize: '1.5rem' }}>{child.avatar}</span>
              {child.name} (Grade {child.grade})
            </ChildCard>
          ))}
        </ChildSelector>

        {selectedChildData?.name === 'Lucas' && (
          <AlertCard
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <AlertIcon>⚠️</AlertIcon>
            <AlertText>
              Lucas hasn't practiced in 3 days. Consider encouraging him to maintain his learning streak!
            </AlertText>
          </AlertCard>
        )}

        <DashboardGrid>
          <InfoCard whileHover={{ y: -5 }}>
            <CardTitle>
              📊 Quick Overview
            </CardTitle>
            <QuickStats>
              <StatRow>
                <StatLabel>Study Streak</StatLabel>
                <StatValue>{selectedChildData?.name === 'Emma' ? '5 days' : '0 days'}</StatValue>
              </StatRow>
              <StatRow>
                <StatLabel>Weekly Progress</StatLabel>
                <StatValue>{selectedChildData?.name === 'Emma' ? '85%' : '45%'}</StatValue>
              </StatRow>
              <StatRow>
                <StatLabel>Questions This Week</StatLabel>
                <StatValue>{selectedChildData?.name === 'Emma' ? '142' : '67'}</StatValue>
              </StatRow>
              <StatRow>
                <StatLabel>Average Accuracy</StatLabel>
                <StatValue>{selectedChildData?.name === 'Emma' ? '88%' : '72%'}</StatValue>
              </StatRow>
              <StatRow>
                <StatLabel>Strongest Subject</StatLabel>
                <StatValue>{selectedChildData?.name === 'Emma' ? 'Reading' : 'Math'}</StatValue>
              </StatRow>
            </QuickStats>
          </InfoCard>

          <InfoCard whileHover={{ y: -5 }}>
            <CardTitle>
              🎯 Weekly Goals
            </CardTitle>
            <LearningGoals>
              {weeklyGoals.map(goal => (
                <GoalItem key={goal.id}>
                  <GoalCheckbox checked={goal.checked}>
                    {goal.checked && '✓'}
                  </GoalCheckbox>
                  <GoalText checked={goal.checked}>
                    {goal.text}
                  </GoalText>
                </GoalItem>
              ))}
            </LearningGoals>
            <ActionButtons>
              <SecondaryButton
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                📝 Edit Goals
              </SecondaryButton>
            </ActionButtons>
          </InfoCard>

          <InfoCard whileHover={{ y: -5 }}>
            <CardTitle>
              🕐 Recent Activity
            </CardTitle>
            <RecentActivity>
              {recentActivities.map((activity, index) => (
                <ActivityItem key={index}>
                  <ActivityIcon>{activity.icon}</ActivityIcon>
                  <ActivityDetails>
                    <ActivityTitle>{activity.title}</ActivityTitle>
                    <ActivityTime>{activity.time}</ActivityTime>
                  </ActivityDetails>
                </ActivityItem>
              ))}
            </RecentActivity>
          </InfoCard>

          <InfoCard whileHover={{ y: -5 }} style={{ gridColumn: 'span 3' }}>
            <CardTitle>
              🎮 Parent Actions
            </CardTitle>
            <ActionButtons>
              <PrimaryButton
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => onNavigate('learning')}
              >
                📈 View Detailed Report
              </PrimaryButton>
              <SecondaryButton
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                ⏰ Set Study Schedule
              </SecondaryButton>
              <SecondaryButton
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                🎯 Customize Learning Path
              </SecondaryButton>
              <SecondaryButton
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                💬 Send Encouragement
              </SecondaryButton>
            </ActionButtons>
          </InfoCard>
        </DashboardGrid>
      </Content>
    </Container>
  );
};

export default ParentDashboard;