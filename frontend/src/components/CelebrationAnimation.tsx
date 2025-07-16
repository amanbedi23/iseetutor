import React, { useEffect, useState } from 'react';
import styled from '@emotion/styled';
import { motion, AnimatePresence } from 'framer-motion';

const CelebrationContainer = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 9999;
`;

const ConfettiPiece = styled(motion.div)<{ color: string }>`
  position: absolute;
  width: 10px;
  height: 10px;
  background: ${props => props.color};
  border-radius: 2px;
`;

const Star = styled(motion.div)`
  position: absolute;
  font-size: 2rem;
`;

const CelebrationText = styled(motion.div)`
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 4rem;
  font-weight: bold;
  color: #ffd700;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
  z-index: 10000;
  pointer-events: none;
`;

const FireworkContainer = styled.svg`
  position: fixed;
  width: 100%;
  height: 100%;
  pointer-events: none;
`;

const colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#ffd93d', '#6bcf7f', '#e056fd'];

interface CelebrationAnimationProps {
  type: 'confetti' | 'stars' | 'fireworks' | 'all';
  duration?: number;
  text?: string;
  onComplete?: () => void;
}

export const CelebrationAnimation: React.FC<CelebrationAnimationProps> = ({
  type = 'confetti',
  duration = 3000,
  text,
  onComplete,
}) => {
  const [particles, setParticles] = useState<any[]>([]);
  const [showAnimation, setShowAnimation] = useState(true);

  useEffect(() => {
    generateParticles();
    const timer = setTimeout(() => {
      setShowAnimation(false);
      if (onComplete) onComplete();
    }, duration);

    return () => clearTimeout(timer);
  }, [duration, onComplete]);

  const generateParticles = () => {
    const newParticles = [];
    const count = type === 'all' ? 100 : 50;

    for (let i = 0; i < count; i++) {
      newParticles.push({
        id: i,
        x: Math.random() * window.innerWidth,
        y: -20,
        color: colors[Math.floor(Math.random() * colors.length)],
        rotation: Math.random() * 360,
        size: Math.random() * 10 + 5,
      });
    }
    setParticles(newParticles);
  };

  const renderConfetti = () => (
    <>
      {particles.map((particle) => (
        <ConfettiPiece
          key={particle.id}
          color={particle.color}
          initial={{
            x: particle.x,
            y: particle.y,
            rotate: particle.rotation,
            scale: 0,
          }}
          animate={{
            x: particle.x + (Math.random() - 0.5) * 200,
            y: window.innerHeight + 50,
            rotate: particle.rotation + Math.random() * 720,
            scale: [0, 1, 1, 0],
          }}
          transition={{
            duration: duration / 1000,
            ease: 'easeOut',
            times: [0, 0.1, 0.9, 1],
          }}
          style={{
            width: particle.size,
            height: particle.size,
          }}
        />
      ))}
    </>
  );

  const renderStars = () => (
    <>
      {particles.slice(0, 20).map((particle) => (
        <Star
          key={particle.id}
          initial={{
            x: particle.x,
            y: particle.y,
            scale: 0,
            opacity: 0,
          }}
          animate={{
            x: particle.x + (Math.random() - 0.5) * 100,
            y: particle.y + Math.random() * 200,
            scale: [0, 1.5, 0],
            opacity: [0, 1, 0],
            rotate: [0, 180, 360],
          }}
          transition={{
            duration: duration / 1000,
            ease: 'easeOut',
          }}
        >
          ⭐
        </Star>
      ))}
    </>
  );

  const renderFireworks = () => (
    <FireworkContainer>
      {particles.slice(0, 5).map((particle, index) => {
        const cx = particle.x;
        const cy = window.innerHeight / 2 + (Math.random() - 0.5) * 200;
        const sparkCount = 12;
        
        return (
          <g key={particle.id}>
            {/* Firework trail */}
            <motion.line
              x1={cx}
              y1={window.innerHeight}
              x2={cx}
              y2={cy}
              stroke={particle.color}
              strokeWidth="3"
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ duration: 0.5, delay: index * 0.2 }}
            />
            
            {/* Explosion */}
            {Array.from({ length: sparkCount }).map((_, i) => {
              const angle = (i / sparkCount) * Math.PI * 2;
              const distance = 100;
              const endX = cx + Math.cos(angle) * distance;
              const endY = cy + Math.sin(angle) * distance;
              
              return (
                <motion.line
                  key={i}
                  x1={cx}
                  y1={cy}
                  x2={endX}
                  y2={endY}
                  stroke={particle.color}
                  strokeWidth="2"
                  initial={{ opacity: 0, pathLength: 0 }}
                  animate={{ 
                    opacity: [0, 1, 0],
                    pathLength: [0, 1, 1],
                  }}
                  transition={{ 
                    duration: 1,
                    delay: index * 0.2 + 0.5,
                    ease: 'easeOut'
                  }}
                />
              );
            })}
            
            {/* Center burst */}
            <motion.circle
              cx={cx}
              cy={cy}
              r="5"
              fill={particle.color}
              initial={{ scale: 0, opacity: 0 }}
              animate={{ 
                scale: [0, 3, 0],
                opacity: [0, 1, 0]
              }}
              transition={{ 
                duration: 0.5,
                delay: index * 0.2 + 0.5
              }}
            />
          </g>
        );
      })}
    </FireworkContainer>
  );

  const renderAll = () => (
    <>
      {renderConfetti()}
      {renderStars()}
      {renderFireworks()}
    </>
  );

  return (
    <AnimatePresence>
      {showAnimation && (
        <>
          <CelebrationContainer>
            {type === 'confetti' && renderConfetti()}
            {type === 'stars' && renderStars()}
            {type === 'fireworks' && renderFireworks()}
            {type === 'all' && renderAll()}
          </CelebrationContainer>
          
          {text && (
            <CelebrationText
              initial={{ scale: 0, rotate: -10 }}
              animate={{ 
                scale: [0, 1.2, 1],
                rotate: [-10, 5, 0]
              }}
              exit={{ scale: 0, opacity: 0 }}
              transition={{ 
                duration: 0.5,
                type: 'spring',
                stiffness: 200
              }}
            >
              {text}
            </CelebrationText>
          )}
        </>
      )}
    </AnimatePresence>
  );
};

// Hook for easy use
export const useCelebration = () => {
  const [celebration, setCelebration] = useState<{
    show: boolean;
    type: 'confetti' | 'stars' | 'fireworks' | 'all';
    text?: string;
  }>({ show: false, type: 'confetti' });

  const celebrate = (
    type: 'confetti' | 'stars' | 'fireworks' | 'all' = 'confetti',
    text?: string,
    duration = 3000
  ) => {
    setCelebration({ show: true, type, text });
    setTimeout(() => {
      setCelebration({ show: false, type: 'confetti' });
    }, duration);
  };

  return { celebration, celebrate };
};