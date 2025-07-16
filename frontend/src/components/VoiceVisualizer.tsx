import React, { useEffect, useRef } from 'react';
import styled from '@emotion/styled';
import { motion } from 'framer-motion';

const Container = styled.div`
  position: relative;
  width: 300px;
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
`;

const Canvas = styled.canvas`
  position: absolute;
  width: 100%;
  height: 100%;
`;

const CenterOrb = styled(motion.div)<{ isActive: boolean }>`
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: ${props => props.isActive 
    ? 'radial-gradient(circle, rgba(255,255,255,0.9) 0%, rgba(255,255,255,0.3) 100%)' 
    : 'radial-gradient(circle, rgba(255,255,255,0.5) 0%, rgba(255,255,255,0.1) 100%)'};
  box-shadow: 0 0 40px rgba(255, 255, 255, 0.4);
  z-index: 1;
`;

interface VoiceVisualizerProps {
  isActive: boolean;
  audioLevel?: number;
  color?: string;
}

// Define Particle interface for type safety
interface IParticle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  life: number;
  maxLife: number;
  update: () => void;
  draw: (ctx: CanvasRenderingContext2D) => void;
  isAlive: () => boolean;
}

const VoiceVisualizer: React.FC<VoiceVisualizerProps> = ({ 
  isActive, 
  audioLevel = 0,
  color = '#ffffff' 
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number | null>(null);
  const particlesRef = useRef<IParticle[]>([]);

  useEffect(() => {
    // Define Particle class inside useEffect to avoid dependency issues
    class Particle implements IParticle {
      x: number;
      y: number;
      vx: number;
      vy: number;
      size: number;
      life: number;
      maxLife: number;

      constructor(centerX: number, centerY: number) {
        const angle = Math.random() * Math.PI * 2;
        const distance = 60 + Math.random() * 20;
        this.x = centerX + Math.cos(angle) * distance;
        this.y = centerY + Math.sin(angle) * distance;
        this.vx = Math.cos(angle) * (0.5 + Math.random() * 1.5);
        this.vy = Math.sin(angle) * (0.5 + Math.random() * 1.5);
        this.size = 2 + Math.random() * 3;
        this.life = 0;
        this.maxLife = 60 + Math.random() * 40;
      }

      update() {
        this.x += this.vx;
        this.y += this.vy;
        this.life++;
        this.vx *= 0.98;
        this.vy *= 0.98;
      }

      draw(ctx: CanvasRenderingContext2D) {
        const lifeRatio = 1 - (this.life / this.maxLife);
        ctx.globalAlpha = lifeRatio * 0.6;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size * lifeRatio, 0, Math.PI * 2);
        ctx.fill();
      }

      isAlive() {
        return this.life < this.maxLife;
      }
    }

    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    canvas.width = 300;
    canvas.height = 300;

    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;

    // Animation loop
    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      // Add new particles when active
      if (isActive && Math.random() < 0.3 + audioLevel * 0.5) {
        for (let i = 0; i < 2 + Math.floor(audioLevel * 3); i++) {
          particlesRef.current.push(new Particle(centerX, centerY));
        }
      }

      // Update and draw particles
      ctx.fillStyle = color;
      particlesRef.current = particlesRef.current.filter(particle => {
        particle.update();
        if (particle.isAlive()) {
          particle.draw(ctx);
          return true;
        }
        return false;
      });

      // Draw circular waveform
      if (isActive) {
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.globalAlpha = 0.3 + audioLevel * 0.4;
        
        // Draw multiple circles with different radii
        for (let i = 0; i < 3; i++) {
          ctx.beginPath();
          const radius = 70 + i * 20 + audioLevel * 30 * (1 + i * 0.3);
          const segments = 32;
          
          for (let j = 0; j <= segments; j++) {
            const angle = (j / segments) * Math.PI * 2;
            const noise = Math.sin(Date.now() * 0.001 + j * 0.5) * audioLevel * 10;
            const r = radius + noise;
            const x = centerX + Math.cos(angle) * r;
            const y = centerY + Math.sin(angle) * r;
            
            if (j === 0) {
              ctx.moveTo(x, y);
            } else {
              ctx.lineTo(x, y);
            }
          }
          
          ctx.closePath();
          ctx.stroke();
        }
      }

      animationRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isActive, audioLevel, color]);

  return (
    <Container>
      <Canvas ref={canvasRef} />
      <CenterOrb
        isActive={isActive}
        animate={{
          scale: isActive ? [1, 1.1, 1] : 1,
          opacity: isActive ? [0.8, 1, 0.8] : 0.5,
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      />
    </Container>
  );
};

export default VoiceVisualizer;