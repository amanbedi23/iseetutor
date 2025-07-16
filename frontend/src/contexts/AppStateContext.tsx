import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface User {
  id: string;
  name: string;
  age: number;
  gradeLevel: number;
  progress: {
    questionsAnswered: number;
    correctAnswers: number;
    topicsStudied: string[];
  };
}

interface AppState {
  user: User | null;
  mode: 'tutor' | 'friend' | 'hybrid';
  isListening: boolean;
  isSpeaking: boolean;
  isThinking: boolean;
  volume: number;
  isMuted: boolean;
}

interface AppStateContextType extends AppState {
  setUser: (user: User | null) => void;
  setMode: (mode: 'tutor' | 'friend' | 'hybrid') => void;
  setListening: (listening: boolean) => void;
  setSpeaking: (speaking: boolean) => void;
  setThinking: (thinking: boolean) => void;
  setVolume: (volume: number) => void;
  toggleMute: () => void;
}

const AppStateContext = createContext<AppStateContextType | undefined>(undefined);

export const useAppState = () => {
  const context = useContext(AppStateContext);
  if (!context) {
    throw new Error('useAppState must be used within AppStateProvider');
  }
  return context;
};

interface AppStateProviderProps {
  children: ReactNode;
}

export const AppStateProvider: React.FC<AppStateProviderProps> = ({ children }) => {
  const [state, setState] = useState<AppState>({
    user: null,
    mode: 'hybrid',
    isListening: false,
    isSpeaking: false,
    isThinking: false,
    volume: 0.8,
    isMuted: false,
  });

  // Load persisted state
  useEffect(() => {
    const savedState = localStorage.getItem('isee-tutor-state');
    if (savedState) {
      try {
        const parsed = JSON.parse(savedState);
        setState(prev => ({ ...prev, ...parsed }));
      } catch (error) {
        console.error('Failed to load saved state:', error);
      }
    }
  }, []);

  // Save state changes
  useEffect(() => {
    const { user, mode, volume, isMuted } = state;
    localStorage.setItem('isee-tutor-state', JSON.stringify({
      user,
      mode,
      volume,
      isMuted
    }));
  }, [state.user, state.mode, state.volume, state.isMuted]); // eslint-disable-line react-hooks/exhaustive-deps

  const contextValue: AppStateContextType = {
    ...state,
    setUser: (user) => setState(prev => ({ ...prev, user })),
    setMode: (mode) => setState(prev => ({ ...prev, mode })),
    setListening: (isListening) => setState(prev => ({ ...prev, isListening })),
    setSpeaking: (isSpeaking) => setState(prev => ({ ...prev, isSpeaking })),
    setThinking: (isThinking) => setState(prev => ({ ...prev, isThinking })),
    setVolume: (volume) => setState(prev => ({ ...prev, volume })),
    toggleMute: () => setState(prev => ({ ...prev, isMuted: !prev.isMuted })),
  };

  return (
    <AppStateContext.Provider value={contextValue}>
      {children}
    </AppStateContext.Provider>
  );
};