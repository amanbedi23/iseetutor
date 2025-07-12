import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { io, Socket } from 'socket.io-client';
import { useAppState } from './AppStateContext';

interface WebSocketContextType {
  socket: Socket | null;
  connected: boolean;
  sendMessage: (event: string, data: any) => void;
  onMessage: (event: string, handler: (data: any) => void) => () => void;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within WebSocketProvider');
  }
  return context;
};

interface WebSocketProviderProps {
  children: ReactNode;
}

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({ children }) => {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [connected, setConnected] = useState(false);
  const { setListening, setSpeaking, setThinking } = useAppState();

  useEffect(() => {
    const socketUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';
    const newSocket = io(socketUrl, {
      transports: ['websocket'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5,
    });

    newSocket.on('connect', () => {
      console.log('WebSocket connected');
      setConnected(true);
    });

    newSocket.on('disconnect', () => {
      console.log('WebSocket disconnected');
      setConnected(false);
    });

    // Handle state updates from server
    newSocket.on('state_update', (data: any) => {
      if (data.isListening !== undefined) setListening(data.isListening);
      if (data.isSpeaking !== undefined) setSpeaking(data.isSpeaking);
      if (data.isThinking !== undefined) setThinking(data.isThinking);
    });

    setSocket(newSocket);

    return () => {
      newSocket.close();
    };
  }, []);

  const sendMessage = (event: string, data: any) => {
    if (socket && connected) {
      socket.emit(event, data);
    }
  };

  const onMessage = (event: string, handler: (data: any) => void) => {
    if (!socket) return () => {};
    
    socket.on(event, handler);
    return () => {
      socket.off(event, handler);
    };
  };

  const contextValue: WebSocketContextType = {
    socket,
    connected,
    sendMessage,
    onMessage,
  };

  return (
    <WebSocketContext.Provider value={contextValue}>
      {children}
    </WebSocketContext.Provider>
  );
};