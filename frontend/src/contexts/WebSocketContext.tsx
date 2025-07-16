import React, { createContext, useContext, useEffect, useState, useRef, ReactNode } from 'react';
import { useAppState } from './AppStateContext';

interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

interface WebSocketContextType {
  ws: WebSocket | null;
  connected: boolean;
  sendMessage: (message: WebSocketMessage) => void;
  onMessage: (type: string, handler: (data: any) => void) => () => void;
  startVoicePipeline: (mode?: string) => void;
  stopVoicePipeline: () => void;
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
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const { setListening, setSpeaking, setThinking, mode } = useAppState();
  const messageHandlers = useRef<Map<string, Set<(data: any) => void>>>(new Map());
  const reconnectTimeout = useRef<NodeJS.Timeout | null>(null);

  const connect = () => {
    // Dynamically determine WebSocket URL based on current location
    const host = window.location.hostname;
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${host}:8000/ws`;
    console.log('Connecting to WebSocket:', wsUrl);
    
    const newWs = new WebSocket(wsUrl);

    newWs.onopen = () => {
      console.log('WebSocket connected');
      setConnected(true);
      setWs(newWs);
    };

    newWs.onclose = () => {
      console.log('WebSocket disconnected');
      setConnected(false);
      setWs(null);
      
      // Attempt to reconnect after 2 seconds
      reconnectTimeout.current = setTimeout(() => {
        console.log('Attempting to reconnect...');
        connect();
      }, 2000);
    };

    newWs.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    newWs.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        console.log('WebSocket message:', message);

        // Handle voice pipeline state updates
        if (message.type === 'voice_state') {
          const state = message.state;
          setListening(state === 'recording');
          setThinking(state === 'processing');
          setSpeaking(state === 'speaking');
        }

        // Dispatch to registered handlers
        const handlers = messageHandlers.current.get(message.type);
        if (handlers) {
          handlers.forEach(handler => {
            try {
              handler(message);
            } catch (error) {
              console.error('Error in message handler:', error);
            }
          });
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    return newWs;
  };

  useEffect(() => {
    const websocket = connect();

    return () => {
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
      if (websocket.readyState === WebSocket.OPEN) {
        websocket.close();
      }
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const sendMessage = (message: WebSocketMessage) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected, cannot send message:', message);
    }
  };

  const onMessage = (type: string, handler: (data: any) => void) => {
    if (!messageHandlers.current.has(type)) {
      messageHandlers.current.set(type, new Set());
    }
    messageHandlers.current.get(type)!.add(handler);

    // Return cleanup function
    return () => {
      const handlers = messageHandlers.current.get(type);
      if (handlers) {
        handlers.delete(handler);
        if (handlers.size === 0) {
          messageHandlers.current.delete(type);
        }
      }
    };
  };

  const startVoicePipeline = (overrideMode?: string) => {
    sendMessage({
      type: 'voice_start',
      mode: overrideMode || mode
    });
  };

  const stopVoicePipeline = () => {
    sendMessage({
      type: 'voice_stop'
    });
  };

  const contextValue: WebSocketContextType = {
    ws,
    connected,
    sendMessage,
    onMessage,
    startVoicePipeline,
    stopVoicePipeline,
  };

  return (
    <WebSocketContext.Provider value={contextValue}>
      {children}
    </WebSocketContext.Provider>
  );
};