'use client';

import { createContext, useContext, ReactNode } from 'react';
import { useWebSocket, type WSStatus } from '@/hooks/useWebSocket';

interface WebSocketContextValue {
  status: WSStatus;
  send: (data: unknown) => void;
}

const WebSocketContext = createContext<WebSocketContextValue | null>(null);

interface WebSocketProviderProps {
  url: string | null;
  children: ReactNode;
  onMessage?: (event: MessageEvent) => void;
}

export function WebSocketProvider({
  url,
  children,
  onMessage,
}: WebSocketProviderProps) {
  const { status, send } = useWebSocket(url, { onMessage });

  return (
    <WebSocketContext.Provider value={{ status, send }}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocketContext(): WebSocketContextValue {
  const ctx = useContext(WebSocketContext);
  if (!ctx)
    throw new Error(
      'useWebSocketContext must be used within WebSocketProvider',
    );
  return ctx;
}
