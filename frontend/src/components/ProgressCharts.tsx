import React, { useState } from 'react';
import styled from '@emotion/styled';
import { motion } from 'framer-motion';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from 'recharts';

const ChartsContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 2rem;
  margin-top: 2rem;
`;

const ChartCard = styled(motion.div)`
  background: white;
  border-radius: 15px;
  padding: 1.5rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  
  &:hover {
    box-shadow: 0 8px 15px rgba(0, 0, 0, 0.1);
  }
`;

const ChartTitle = styled.h3`
  font-size: 1.2rem;
  color: #2d3748;
  margin-bottom: 1rem;
  font-weight: 600;
`;

const TimeRangeSelector = styled.div`
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
`;

const TimeButton = styled.button<{ active: boolean }>`
  padding: 0.4rem 0.8rem;
  border: none;
  border-radius: 5px;
  background: ${props => props.active ? '#667eea' : '#e2e8f0'};
  color: ${props => props.active ? 'white' : '#4a5568'};
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.2s;
  
  &:hover {
    background: ${props => props.active ? '#5a67d8' : '#cbd5e0'};
  }
`;

const COLORS = ['#667eea', '#764ba2', '#48bb78', '#ed8936', '#38b2ac'];

interface ProgressData {
  date: string;
  accuracy: number;
  questions: number;
  time: number;
}

interface SubjectData {
  subject: string;
  mastery: number;
  fullMark: 100;
}

interface TopicDistribution {
  name: string;
  value: number;
}

interface ProgressChartsProps {
  userId?: string;
}

const ProgressCharts: React.FC<ProgressChartsProps> = ({ userId }) => {
  const [timeRange, setTimeRange] = useState<'week' | 'month' | '3months'>('week');

  // Demo data - in production, this would come from the API
  const progressData: ProgressData[] = [
    { date: 'Mon', accuracy: 75, questions: 20, time: 35 },
    { date: 'Tue', accuracy: 82, questions: 25, time: 42 },
    { date: 'Wed', accuracy: 79, questions: 18, time: 30 },
    { date: 'Thu', accuracy: 85, questions: 30, time: 50 },
    { date: 'Fri', accuracy: 88, questions: 28, time: 45 },
    { date: 'Sat', accuracy: 83, questions: 22, time: 38 },
    { date: 'Sun', accuracy: 90, questions: 35, time: 55 },
  ];

  const subjectData: SubjectData[] = [
    { subject: 'Verbal', mastery: 75, fullMark: 100 },
    { subject: 'Math', mastery: 68, fullMark: 100 },
    { subject: 'Reading', mastery: 85, fullMark: 100 },
    { subject: 'Quantitative', mastery: 72, fullMark: 100 },
    { subject: 'Writing', mastery: 60, fullMark: 100 },
  ];

  const topicDistribution: TopicDistribution[] = [
    { name: 'Vocabulary', value: 25 },
    { name: 'Algebra', value: 20 },
    { name: 'Geometry', value: 15 },
    { name: 'Reading Comp', value: 30 },
    { name: 'Grammar', value: 10 },
  ];

  const weeklyGoals = {
    questionsTarget: 150,
    questionsCompleted: 178,
    timeTarget: 300, // minutes
    timeCompleted: 295,
    accuracyTarget: 80,
    currentAccuracy: 83,
  };

  return (
    <ChartsContainer>
      {/* Accuracy Trend Chart */}
      <ChartCard whileHover={{ y: -5 }}>
        <TimeRangeSelector>
          <TimeButton 
            active={timeRange === 'week'} 
            onClick={() => setTimeRange('week')}
          >
            Week
          </TimeButton>
          <TimeButton 
            active={timeRange === 'month'} 
            onClick={() => setTimeRange('month')}
          >
            Month
          </TimeButton>
          <TimeButton 
            active={timeRange === '3months'} 
            onClick={() => setTimeRange('3months')}
          >
            3 Months
          </TimeButton>
        </TimeRangeSelector>
        <ChartTitle>Accuracy Trend</ChartTitle>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={progressData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="date" stroke="#718096" />
            <YAxis stroke="#718096" domain={[0, 100]} />
            <Tooltip 
              contentStyle={{ 
                background: 'white', 
                border: '1px solid #e2e8f0',
                borderRadius: '8px'
              }}
            />
            <Line 
              type="monotone" 
              dataKey="accuracy" 
              stroke="#667eea" 
              strokeWidth={3}
              dot={{ fill: '#667eea', r: 6 }}
              activeDot={{ r: 8 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </ChartCard>

      {/* Subject Mastery Radar Chart */}
      <ChartCard whileHover={{ y: -5 }}>
        <ChartTitle>Subject Mastery</ChartTitle>
        <ResponsiveContainer width="100%" height={300}>
          <RadarChart data={subjectData}>
            <PolarGrid stroke="#e2e8f0" />
            <PolarAngleAxis dataKey="subject" stroke="#718096" />
            <PolarRadiusAxis angle={90} domain={[0, 100]} stroke="#718096" />
            <Radar 
              name="Mastery" 
              dataKey="mastery" 
              stroke="#764ba2" 
              fill="#764ba2" 
              fillOpacity={0.6}
            />
            <Tooltip />
          </RadarChart>
        </ResponsiveContainer>
      </ChartCard>

      {/* Daily Activity Chart */}
      <ChartCard whileHover={{ y: -5 }}>
        <ChartTitle>Daily Activity</ChartTitle>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={progressData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="date" stroke="#718096" />
            <YAxis stroke="#718096" />
            <Tooltip 
              contentStyle={{ 
                background: 'white', 
                border: '1px solid #e2e8f0',
                borderRadius: '8px'
              }}
            />
            <Legend />
            <Bar dataKey="questions" fill="#667eea" radius={[8, 8, 0, 0]} />
            <Bar dataKey="time" fill="#48bb78" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>

      {/* Topic Distribution Pie Chart */}
      <ChartCard whileHover={{ y: -5 }}>
        <ChartTitle>Practice Distribution</ChartTitle>
        <ResponsiveContainer width="100%" height={250}>
          <PieChart>
            <Pie
              data={topicDistribution}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {topicDistribution.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </ChartCard>

      {/* Weekly Goals Progress */}
      <ChartCard whileHover={{ y: -5 }} style={{ gridColumn: 'span 2' }}>
        <ChartTitle>Weekly Goals</ChartTitle>
        <GoalsContainer>
          <GoalItem>
            <GoalLabel>Questions Completed</GoalLabel>
            <GoalProgress>
              <GoalBar>
                <GoalFill 
                  width={(weeklyGoals.questionsCompleted / weeklyGoals.questionsTarget) * 100}
                  exceeded={weeklyGoals.questionsCompleted > weeklyGoals.questionsTarget}
                />
              </GoalBar>
              <GoalText>
                {weeklyGoals.questionsCompleted} / {weeklyGoals.questionsTarget}
              </GoalText>
            </GoalProgress>
          </GoalItem>

          <GoalItem>
            <GoalLabel>Study Time (minutes)</GoalLabel>
            <GoalProgress>
              <GoalBar>
                <GoalFill 
                  width={(weeklyGoals.timeCompleted / weeklyGoals.timeTarget) * 100}
                  exceeded={weeklyGoals.timeCompleted > weeklyGoals.timeTarget}
                />
              </GoalBar>
              <GoalText>
                {weeklyGoals.timeCompleted} / {weeklyGoals.timeTarget}
              </GoalText>
            </GoalProgress>
          </GoalItem>

          <GoalItem>
            <GoalLabel>Accuracy Target</GoalLabel>
            <GoalProgress>
              <GoalBar>
                <GoalFill 
                  width={(weeklyGoals.currentAccuracy / weeklyGoals.accuracyTarget) * 100}
                  exceeded={weeklyGoals.currentAccuracy > weeklyGoals.accuracyTarget}
                />
              </GoalBar>
              <GoalText>
                {weeklyGoals.currentAccuracy}% / {weeklyGoals.accuracyTarget}%
              </GoalText>
            </GoalProgress>
          </GoalItem>
        </GoalsContainer>
      </ChartCard>
    </ChartsContainer>
  );
};

// Weekly Goals Styles
const GoalsContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
`;

const GoalItem = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
`;

const GoalLabel = styled.div`
  color: #4a5568;
  font-size: 0.9rem;
  font-weight: 500;
`;

const GoalProgress = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
`;

const GoalBar = styled.div`
  flex: 1;
  height: 20px;
  background: #e2e8f0;
  border-radius: 10px;
  overflow: hidden;
`;

const GoalFill = styled(motion.div)<{ width: number; exceeded: boolean }>`
  height: 100%;
  background: ${props => props.exceeded ? '#48bb78' : '#667eea'};
  width: ${props => Math.min(props.width, 100)}%;
  transition: width 0.5s ease;
`;

const GoalText = styled.div`
  color: #2d3748;
  font-size: 0.9rem;
  font-weight: 600;
  min-width: 80px;
`;

export default ProgressCharts;