import React, { useEffect, useState } from 'react';
import styled from '@emotion/styled';
import { AnimatePresence } from 'framer-motion';
import HomeScreen from './components/HomeScreen';
import VoiceInteraction from './components/VoiceInteraction';
import LearningDashboard from './components/LearningDashboard';
import { WebSocketProvider } from './contexts/WebSocketContext';
import { AudioProvider } from './contexts/AudioContext';
import { AppStateProvider } from './contexts/AppStateContext';
import GlobalStyles from './styles/GlobalStyles';

const AppContainer = styled.div<{ idle: boolean }>`
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
  cursor: ${props => props.idle ? 'none' : 'auto'};
`;

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<'home' | 'voice' | 'learning'>('home');
  const [isIdle, setIsIdle] = useState(false);
  const [idleTimer, setIdleTimer] = useState<NodeJS.Timeout | null>(null);

  // Reset idle timer on activity
  const resetIdleTimer = () => {
    setIsIdle(false);
    if (idleTimer) clearTimeout(idleTimer);
    const timer = setTimeout(() => setIsIdle(true), 3000);
    setIdleTimer(timer);
  };

  useEffect(() => {
    // Initialize idle timer
    resetIdleTimer();

    // Add event listeners for activity
    const events = ['mousemove', 'keydown', 'wheel', 'touchstart'];
    events.forEach(event => {
      document.addEventListener(event, resetIdleTimer);
    });

    return () => {
      events.forEach(event => {
        document.removeEventListener(event, resetIdleTimer);
      });
      if (idleTimer) clearTimeout(idleTimer);
    };
  }, []);

  // Prevent right-click context menu
  useEffect(() => {
    const preventContextMenu = (e: MouseEvent) => e.preventDefault();
    document.addEventListener('contextmenu', preventContextMenu);
    return () => document.removeEventListener('contextmenu', preventContextMenu);
  }, []);

  // Prevent navigation away (back button, refresh)
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      e.returnValue = '';
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, []);

  // Auto-recovery: reload on critical errors
  useEffect(() => {
    const handleError = (event: ErrorEvent) => {
      console.error('Critical error:', event.error);
      // In production, reload after 5 seconds
      if (process.env.NODE_ENV === 'production') {
        setTimeout(() => window.location.reload(), 5000);
      }
    };
    window.addEventListener('error', handleError);
    return () => window.removeEventListener('error', handleError);
  }, []);

  // Request fullscreen on load (user interaction required)
  useEffect(() => {
    const requestFullscreen = async () => {
      try {
        if (!document.fullscreenElement && document.documentElement.requestFullscreen) {
          await document.documentElement.requestFullscreen();
        }
      } catch (err) {
        console.log('Fullscreen request failed:', err);
      }
    };

    // Request on first user interaction
    const handleFirstInteraction = () => {
      requestFullscreen();
      document.removeEventListener('click', handleFirstInteraction);
      document.removeEventListener('touchstart', handleFirstInteraction);
    };

    document.addEventListener('click', handleFirstInteraction);
    document.addEventListener('touchstart', handleFirstInteraction);

    return () => {
      document.removeEventListener('click', handleFirstInteraction);
      document.removeEventListener('touchstart', handleFirstInteraction);
    };
  }, []);

  return (
    <AppStateProvider>
      <WebSocketProvider>
        <AudioProvider>
          <GlobalStyles />
          <AppContainer idle={isIdle}>
            <AnimatePresence mode="wait">
              {currentView === 'home' && (
                <HomeScreen 
                  key="home"
                  onNavigate={setCurrentView} 
                />
              )}
              {currentView === 'voice' && (
                <VoiceInteraction 
                  key="voice"
                  onNavigate={setCurrentView} 
                />
              )}
              {currentView === 'learning' && (
                <LearningDashboard 
                  key="learning"
                  onNavigate={setCurrentView} 
                />
              )}
            </AnimatePresence>
          </AppContainer>
        </AudioProvider>
      </WebSocketProvider>
    </AppStateProvider>
  );
};

export default App;
