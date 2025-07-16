import React from 'react';
import styled from '@emotion/styled';
import { motion } from 'framer-motion';

const StreakContainer = styled(motion.div)`
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  border-radius: 20px;
  padding: 2rem;
  color: white;
  box-shadow: 0 10px 30px rgba(245, 87, 108, 0.3);
  margin-bottom: 2rem;
`;

const StreakHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.5rem;
`;

const StreakTitle = styled.h2`
  font-size: 1.5rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const StreakCount = styled.div`
  font-size: 3rem;
  font-weight: 800;
`;

const StreakLabel = styled.div`
  font-size: 1.1rem;
  opacity: 0.9;
`;

const CalendarGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 0.5rem;
  margin-top: 1.5rem;
`;

const WeekDay = styled.div`
  text-align: center;
  font-size: 0.8rem;
  font-weight: 600;
  opacity: 0.8;
  padding: 0.5rem;
`;

const DayCell = styled(motion.div)<{ 
  isToday?: boolean; 
  hasActivity?: boolean; 
  isFuture?: boolean;
  isCurrentMonth?: boolean;
}>`
  aspect-ratio: 1;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  position: relative;
  background: ${props => {
    if (props.isFuture) return 'rgba(255, 255, 255, 0.1)';
    if (props.hasActivity) return 'rgba(255, 255, 255, 0.9)';
    return 'rgba(255, 255, 255, 0.2)';
  }};
  color: ${props => props.hasActivity ? '#f5576c' : 'rgba(255, 255, 255, 0.8)'};
  opacity: ${props => props.isCurrentMonth ? 1 : 0.5};
  
  ${props => props.isToday && `
    &::after {
      content: '';
      position: absolute;
      inset: -3px;
      border: 3px solid white;
      border-radius: 13px;
    }
  `}
  
  &:hover {
    transform: scale(1.1);
    background: ${props => 
      props.hasActivity ? 'white' : 'rgba(255, 255, 255, 0.3)'
    };
  }
`;

const StreakStats = styled.div`
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 1px solid rgba(255, 255, 255, 0.3);
`;

const StatItem = styled.div`
  text-align: center;
`;

const StatValue = styled.div`
  font-size: 1.8rem;
  font-weight: 700;
  margin-bottom: 0.25rem;
`;

const StatLabel = styled.div`
  font-size: 0.9rem;
  opacity: 0.9;
`;

const MotivationalMessage = styled(motion.div)`
  background: rgba(255, 255, 255, 0.2);
  border-radius: 15px;
  padding: 1rem;
  margin-top: 1.5rem;
  text-align: center;
  font-size: 1.1rem;
  font-weight: 500;
  backdrop-filter: blur(10px);
`;

interface StreakData {
  currentStreak: number;
  longestStreak: number;
  totalDays: number;
  activityDates: string[];
}

interface StreakTrackerProps {
  data?: StreakData;
}

const StreakTracker: React.FC<StreakTrackerProps> = ({ data }) => {
  // Default data for demo
  const streakData = data || {
    currentStreak: 5,
    longestStreak: 12,
    totalDays: 45,
    activityDates: [
      '2025-07-12',
      '2025-07-13',
      '2025-07-14',
      '2025-07-15',
      '2025-07-16',
      '2025-07-10',
      '2025-07-09',
      '2025-07-08',
      '2025-07-06',
      '2025-07-05',
      '2025-07-04',
      '2025-07-03',
      '2025-07-01',
      '2025-06-30',
      '2025-06-29',
      '2025-06-28',
    ]
  };

  const today = new Date();
  const currentMonth = today.getMonth();
  const currentYear = today.getFullYear();
  
  // Get the first day of the month
  const firstDay = new Date(currentYear, currentMonth, 1);
  const startingDayOfWeek = firstDay.getDay();
  
  // Get the number of days in the month
  const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
  
  // Get days from previous month to fill the grid
  const daysInPrevMonth = new Date(currentYear, currentMonth, 0).getDate();
  const prevMonthDays = [];
  for (let i = startingDayOfWeek - 1; i >= 0; i--) {
    prevMonthDays.push({
      day: daysInPrevMonth - i,
      isCurrentMonth: false,
      date: new Date(currentYear, currentMonth - 1, daysInPrevMonth - i)
    });
  }
  
  // Get days for current month
  const currentMonthDays = [];
  for (let i = 1; i <= daysInMonth; i++) {
    currentMonthDays.push({
      day: i,
      isCurrentMonth: true,
      date: new Date(currentYear, currentMonth, i)
    });
  }
  
  // Combine all days
  const allDays = [...prevMonthDays, ...currentMonthDays];
  
  // Add days from next month to complete the grid
  const remainingCells = 42 - allDays.length; // 6 weeks × 7 days
  for (let i = 1; i <= remainingCells; i++) {
    allDays.push({
      day: i,
      isCurrentMonth: false,
      date: new Date(currentYear, currentMonth + 1, i)
    });
  }
  
  const weekDays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  
  const hasActivity = (date: Date) => {
    const dateStr = date.toISOString().split('T')[0];
    return streakData.activityDates.includes(dateStr);
  };
  
  const isToday = (date: Date) => {
    return date.toDateString() === today.toDateString();
  };
  
  const isFuture = (date: Date) => {
    return date > today;
  };

  const getMotivationalMessage = () => {
    const { currentStreak } = streakData;
    if (currentStreak === 0) return "Start your streak today! 💪";
    if (currentStreak < 3) return "Great start! Keep it going! 🌟";
    if (currentStreak < 7) return "You're on fire! Almost a week! 🔥";
    if (currentStreak < 14) return "Amazing! You're unstoppable! 🚀";
    if (currentStreak < 30) return "Incredible dedication! Keep pushing! 💎";
    return "You're a learning champion! 🏆";
  };

  return (
    <StreakContainer
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <StreakHeader>
        <StreakTitle>
          <motion.span
            animate={{ rotate: [0, 20, -20, 0] }}
            transition={{ duration: 2, repeat: Infinity, repeatDelay: 3 }}
          >
            🔥
          </motion.span>
          Daily Streak
        </StreakTitle>
        <div>
          <StreakCount>{streakData.currentStreak}</StreakCount>
          <StreakLabel>days in a row</StreakLabel>
        </div>
      </StreakHeader>

      <CalendarGrid>
        {weekDays.map(day => (
          <WeekDay key={day}>{day}</WeekDay>
        ))}
        {allDays.map((dayInfo, index) => (
          <DayCell
            key={index}
            isToday={isToday(dayInfo.date)}
            hasActivity={hasActivity(dayInfo.date)}
            isFuture={isFuture(dayInfo.date)}
            isCurrentMonth={dayInfo.isCurrentMonth}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.01 }}
          >
            {dayInfo.day}
          </DayCell>
        ))}
      </CalendarGrid>

      <StreakStats>
        <StatItem>
          <StatValue>{streakData.currentStreak}</StatValue>
          <StatLabel>Current Streak</StatLabel>
        </StatItem>
        <StatItem>
          <StatValue>{streakData.longestStreak}</StatValue>
          <StatLabel>Longest Streak</StatLabel>
        </StatItem>
        <StatItem>
          <StatValue>{streakData.totalDays}</StatValue>
          <StatLabel>Total Days</StatLabel>
        </StatItem>
      </StreakStats>

      <MotivationalMessage
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
      >
        {getMotivationalMessage()}
      </MotivationalMessage>
    </StreakContainer>
  );
};

export default StreakTracker;