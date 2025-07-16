import React, { useState } from 'react';
import styled from '@emotion/styled';
import { motion, AnimatePresence } from 'framer-motion';

const BadgesContainer = styled.div`
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

const BadgeGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 1.5rem;
`;

const BadgeCard = styled(motion.div)<{ earned: boolean }>`
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  cursor: pointer;
  opacity: ${props => props.earned ? 1 : 0.4};
  filter: ${props => props.earned ? 'none' : 'grayscale(100%)'};
  transition: all 0.3s;
  
  &:hover {
    transform: ${props => props.earned ? 'scale(1.05)' : 'none'};
  }
`;

const BadgeIcon = styled.div<{ size?: number }>`
  width: ${props => props.size || 80}px;
  height: ${props => props.size || 80}px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: ${props => (props.size || 80) * 0.5}px;
  margin-bottom: 0.5rem;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
  position: relative;
`;

const BadgeName = styled.div`
  font-size: 0.9rem;
  font-weight: 600;
  color: #2d3748;
  margin-bottom: 0.25rem;
`;

const BadgeDescription = styled.div`
  font-size: 0.8rem;
  color: #718096;
`;

const ProgressRing = styled.svg`
  position: absolute;
  top: -4px;
  left: -4px;
  transform: rotate(-90deg);
`;

const Modal = styled(motion.div)`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 2rem;
`;

const ModalContent = styled(motion.div)`
  background: white;
  border-radius: 20px;
  padding: 2rem;
  max-width: 400px;
  width: 100%;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.2);
`;

const ModalBadge = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 1.5rem;
`;

const ModalTitle = styled.h3`
  font-size: 1.5rem;
  color: #2d3748;
  margin-bottom: 0.5rem;
  text-align: center;
`;

const ModalDescription = styled.p`
  color: #4a5568;
  text-align: center;
  margin-bottom: 1rem;
`;

const ProgressInfo = styled.div`
  background: #f7fafc;
  border-radius: 10px;
  padding: 1rem;
  margin-bottom: 1rem;
`;

const CloseButton = styled.button`
  width: 100%;
  padding: 0.8rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  
  &:hover {
    background: #5a67d8;
  }
`;

const CategoryTabs = styled.div`
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
`;

const CategoryTab = styled.button<{ active: boolean }>`
  padding: 0.5rem 1rem;
  border: 2px solid ${props => props.active ? '#667eea' : '#e2e8f0'};
  background: ${props => props.active ? '#667eea' : 'white'};
  color: ${props => props.active ? 'white' : '#4a5568'};
  border-radius: 20px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
  
  &:hover {
    border-color: #667eea;
  }
`;

interface Badge {
  id: string;
  name: string;
  description: string;
  icon: string;
  category: 'academic' | 'streak' | 'social' | 'special';
  requirement: string;
  progress?: number;
  maxProgress?: number;
  earned: boolean;
  earnedDate?: string;
}

const badges: Badge[] = [
  // Academic Badges
  {
    id: 'first_question',
    name: 'First Steps',
    description: 'Answer your first question',
    icon: '🎯',
    category: 'academic',
    requirement: 'Answer 1 question',
    progress: 1,
    maxProgress: 1,
    earned: true,
    earnedDate: '2024-01-15'
  },
  {
    id: 'perfect_10',
    name: 'Perfect 10',
    description: 'Get 10 questions correct in a row',
    icon: '⭐',
    category: 'academic',
    requirement: '10 correct answers in a row',
    progress: 10,
    maxProgress: 10,
    earned: true,
    earnedDate: '2024-01-18'
  },
  {
    id: 'math_master',
    name: 'Math Master',
    description: 'Complete 50 math problems',
    icon: '🧮',
    category: 'academic',
    requirement: 'Complete 50 math problems',
    progress: 35,
    maxProgress: 50,
    earned: false
  },
  {
    id: 'vocab_wizard',
    name: 'Vocabulary Wizard',
    description: 'Master 100 vocabulary words',
    icon: '📚',
    category: 'academic',
    requirement: 'Master 100 vocabulary words',
    progress: 78,
    maxProgress: 100,
    earned: false
  },
  {
    id: 'speed_demon',
    name: 'Speed Demon',
    description: 'Complete a quiz in under 5 minutes',
    icon: '⚡',
    category: 'academic',
    requirement: 'Complete quiz < 5 minutes',
    earned: true,
    earnedDate: '2024-01-20'
  },
  
  // Streak Badges
  {
    id: 'week_warrior',
    name: 'Week Warrior',
    description: 'Study for 7 days in a row',
    icon: '🔥',
    category: 'streak',
    requirement: '7 day streak',
    progress: 5,
    maxProgress: 7,
    earned: false
  },
  {
    id: 'month_master',
    name: 'Month Master',
    description: 'Study for 30 days in a row',
    icon: '🏆',
    category: 'streak',
    requirement: '30 day streak',
    progress: 5,
    maxProgress: 30,
    earned: false
  },
  {
    id: 'early_bird',
    name: 'Early Bird',
    description: 'Study before 8 AM for 5 days',
    icon: '🌅',
    category: 'streak',
    requirement: 'Study before 8 AM × 5',
    progress: 2,
    maxProgress: 5,
    earned: false
  },
  
  // Social Badges
  {
    id: 'helper',
    name: 'Helper',
    description: 'Help a friend with a question',
    icon: '🤝',
    category: 'social',
    requirement: 'Help 1 friend',
    earned: false
  },
  {
    id: 'study_buddy',
    name: 'Study Buddy',
    description: 'Complete a study session with a friend',
    icon: '👥',
    category: 'social',
    requirement: 'Study with friend',
    earned: false
  },
  
  // Special Badges
  {
    id: 'explorer',
    name: 'Explorer',
    description: 'Try all learning modes',
    icon: '🗺️',
    category: 'special',
    requirement: 'Try all 3 modes',
    progress: 2,
    maxProgress: 3,
    earned: false
  },
  {
    id: 'night_owl',
    name: 'Night Owl',
    description: 'Study after 9 PM',
    icon: '🦉',
    category: 'special',
    requirement: 'Study after 9 PM',
    earned: true,
    earnedDate: '2024-01-16'
  }
];

const AchievementBadges: React.FC = () => {
  const [selectedBadge, setSelectedBadge] = useState<Badge | null>(null);
  const [activeCategory, setActiveCategory] = useState<'all' | 'academic' | 'streak' | 'social' | 'special'>('all');

  const filteredBadges = activeCategory === 'all' 
    ? badges 
    : badges.filter(badge => badge.category === activeCategory);

  const earnedCount = badges.filter(b => b.earned).length;
  const totalCount = badges.length;

  const renderProgressRing = (progress: number, maxProgress: number, size: number = 88) => {
    const strokeWidth = 4;
    const radius = (size - strokeWidth) / 2;
    const circumference = radius * 2 * Math.PI;
    const offset = circumference - (progress / maxProgress) * circumference;

    return (
      <ProgressRing width={size} height={size}>
        <circle
          stroke="#e2e8f0"
          fill="transparent"
          strokeWidth={strokeWidth}
          r={radius}
          cx={size / 2}
          cy={size / 2}
        />
        <circle
          stroke="#48bb78"
          fill="transparent"
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          r={radius}
          cx={size / 2}
          cy={size / 2}
        />
      </ProgressRing>
    );
  };

  return (
    <>
      <BadgesContainer>
        <SectionTitle>
          Achievements ({earnedCount}/{totalCount})
        </SectionTitle>
        
        <CategoryTabs>
          <CategoryTab 
            active={activeCategory === 'all'} 
            onClick={() => setActiveCategory('all')}
          >
            All
          </CategoryTab>
          <CategoryTab 
            active={activeCategory === 'academic'} 
            onClick={() => setActiveCategory('academic')}
          >
            Academic
          </CategoryTab>
          <CategoryTab 
            active={activeCategory === 'streak'} 
            onClick={() => setActiveCategory('streak')}
          >
            Streaks
          </CategoryTab>
          <CategoryTab 
            active={activeCategory === 'social'} 
            onClick={() => setActiveCategory('social')}
          >
            Social
          </CategoryTab>
          <CategoryTab 
            active={activeCategory === 'special'} 
            onClick={() => setActiveCategory('special')}
          >
            Special
          </CategoryTab>
        </CategoryTabs>

        <BadgeGrid>
          {filteredBadges.map((badge) => (
            <BadgeCard
              key={badge.id}
              earned={badge.earned}
              onClick={() => setSelectedBadge(badge)}
              whileHover={{ y: badge.earned ? -5 : 0 }}
              whileTap={{ scale: 0.95 }}
            >
              <BadgeIcon>
                {badge.progress !== undefined && badge.maxProgress && !badge.earned && (
                  renderProgressRing(badge.progress, badge.maxProgress)
                )}
                {badge.icon}
              </BadgeIcon>
              <BadgeName>{badge.name}</BadgeName>
              {badge.earned && badge.earnedDate && (
                <BadgeDescription>
                  Earned {new Date(badge.earnedDate).toLocaleDateString()}
                </BadgeDescription>
              )}
            </BadgeCard>
          ))}
        </BadgeGrid>
      </BadgesContainer>

      <AnimatePresence>
        {selectedBadge && (
          <Modal
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setSelectedBadge(null)}
          >
            <ModalContent
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              onClick={(e) => e.stopPropagation()}
            >
              <ModalBadge>
                <BadgeIcon size={120}>
                  {selectedBadge.progress !== undefined && 
                   selectedBadge.maxProgress && 
                   !selectedBadge.earned && (
                    renderProgressRing(
                      selectedBadge.progress, 
                      selectedBadge.maxProgress, 
                      128
                    )
                  )}
                  {selectedBadge.icon}
                </BadgeIcon>
              </ModalBadge>

              <ModalTitle>{selectedBadge.name}</ModalTitle>
              <ModalDescription>{selectedBadge.description}</ModalDescription>

              {selectedBadge.earned ? (
                <ProgressInfo>
                  <strong>Earned!</strong> 🎉<br />
                  {selectedBadge.earnedDate && 
                    `Achieved on ${new Date(selectedBadge.earnedDate).toLocaleDateString()}`
                  }
                </ProgressInfo>
              ) : (
                <ProgressInfo>
                  <strong>Requirement:</strong> {selectedBadge.requirement}<br />
                  {selectedBadge.progress !== undefined && selectedBadge.maxProgress && (
                    <>
                      <strong>Progress:</strong> {selectedBadge.progress}/{selectedBadge.maxProgress}
                      <div style={{ 
                        width: '100%', 
                        height: '8px', 
                        background: '#e2e8f0', 
                        borderRadius: '4px',
                        marginTop: '0.5rem'
                      }}>
                        <motion.div
                          style={{
                            width: `${(selectedBadge.progress / selectedBadge.maxProgress) * 100}%`,
                            height: '100%',
                            background: '#48bb78',
                            borderRadius: '4px'
                          }}
                          initial={{ width: 0 }}
                          animate={{ width: `${(selectedBadge.progress / selectedBadge.maxProgress) * 100}%` }}
                        />
                      </div>
                    </>
                  )}
                </ProgressInfo>
              )}

              <CloseButton onClick={() => setSelectedBadge(null)}>
                Close
              </CloseButton>
            </ModalContent>
          </Modal>
        )}
      </AnimatePresence>
    </>
  );
};

export default AchievementBadges;