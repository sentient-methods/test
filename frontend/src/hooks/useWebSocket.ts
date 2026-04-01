import { useCallback, useEffect, useRef, useState } from "react";
import type { SystemResponse } from "../types/messages";

interface UseWebSocketReturn {
  send: (content: string, sessionId?: string) => void;
  lastMessage: SystemResponse | null;
  connected: boolean;
}

export function useWebSocket(url: string): UseWebSocketReturn {
  const ws = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<SystemResponse | null>(null);

  useEffect(() => {
    const socket = new WebSocket(url);

    socket.onopen = () => setConnected(true);
    socket.onclose = () => setConnected(false);
    socket.onerror = () => setConnected(false);

    socket.onmessage = (event) => {
      try {
        const data: SystemResponse = JSON.parse(event.data);
        setLastMessage(data);
      } catch {
        console.error("Failed to parse message:", event.data);
      }
    };

    ws.current = socket;

    return () => {
      socket.close();
    };
  }, [url]);

  const send = useCallback(
    (content: string, sessionId?: string) => {
      if (ws.current?.readyState === WebSocket.OPEN) {
        ws.current.send(
          JSON.stringify({
            content,
            session_id: sessionId ?? null,
            detail_level: "executive",
          })
        );
      }
    },
    []
  );

  return { send, lastMessage, connected };
}
