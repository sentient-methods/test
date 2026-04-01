import { useCallback, useEffect, useRef, useState } from "react";
import type { ChatMessage } from "../types/messages";
import { useWebSocket } from "../hooks/useWebSocket";
import { MessageBubble } from "./MessageBubble";

let messageId = 0;

export function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string | undefined>();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const wsUrl =
    typeof window !== "undefined"
      ? `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}/api/chat`
      : "ws://localhost:8000/api/chat";

  const { send, lastMessage, connected } = useWebSocket(wsUrl);

  // Handle incoming messages
  useEffect(() => {
    if (!lastMessage) return;

    // Capture session ID from metadata
    if (lastMessage.metadata?.session_id) {
      setSessionId(lastMessage.metadata.session_id as string);
    }

    // Skip pure status updates that have no user-facing content
    if (lastMessage.type === "agent_status" && !lastMessage.content) return;

    const msg: ChatMessage = {
      id: `sys-${++messageId}`,
      role: "system",
      content: lastMessage.content,
      agent: lastMessage.agent ?? undefined,
      agentStatus: lastMessage.agent_status ?? undefined,
      type: lastMessage.type,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, msg]);
  }, [lastMessage]);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = useCallback(() => {
    const trimmed = input.trim();
    if (!trimmed) return;

    const msg: ChatMessage = {
      id: `ceo-${++messageId}`,
      role: "ceo",
      content: trimmed,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, msg]);
    send(trimmed, sessionId);
    setInput("");
  }, [input, send, sessionId]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend]
  );

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        maxWidth: "800px",
        margin: "0 auto",
        padding: "0 16px",
      }}
    >
      {/* Header */}
      <header
        style={{
          padding: "20px 0",
          borderBottom: "1px solid rgba(255,255,255,0.08)",
          textAlign: "center",
        }}
      >
        <h1 style={{ fontSize: "20px", fontWeight: 600 }}>MakeItHappen</h1>
        <p style={{ fontSize: "13px", color: "rgba(255,255,255,0.4)", marginTop: "4px" }}>
          As you wish, CEO.{" "}
          <span style={{ color: connected ? "#2ecc71" : "#e74c3c" }}>
            {connected ? "Ready" : "Connecting..."}
          </span>
        </p>
      </header>

      {/* Messages */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "20px 0",
        }}
      >
        {messages.length === 0 && (
          <div
            style={{
              textAlign: "center",
              color: "rgba(255,255,255,0.25)",
              marginTop: "30vh",
            }}
          >
            <p style={{ fontSize: "24px", fontWeight: 300 }}>What would you like to build?</p>
            <p style={{ fontSize: "14px", marginTop: "8px" }}>
              Just tell me what you want. I'll handle the rest.
            </p>
          </div>
        )}
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div
        style={{
          padding: "16px 0",
          borderTop: "1px solid rgba(255,255,255,0.08)",
        }}
      >
        <div
          style={{
            display: "flex",
            gap: "8px",
            alignItems: "flex-end",
          }}
        >
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Tell me what you need..."
            rows={1}
            style={{
              flex: 1,
              padding: "12px 16px",
              borderRadius: "12px",
              border: "1px solid rgba(255,255,255,0.12)",
              background: "rgba(255,255,255,0.06)",
              color: "#e0e0e8",
              fontSize: "14px",
              resize: "none",
              outline: "none",
              fontFamily: "inherit",
            }}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || !connected}
            style={{
              padding: "12px 20px",
              borderRadius: "12px",
              border: "none",
              background:
                input.trim() && connected
                  ? "linear-gradient(135deg, #4a9eff, #3a7bd5)"
                  : "rgba(255,255,255,0.06)",
              color: input.trim() && connected ? "#fff" : "rgba(255,255,255,0.3)",
              fontSize: "14px",
              fontWeight: 600,
              cursor: input.trim() && connected ? "pointer" : "default",
            }}
          >
            Go
          </button>
        </div>
      </div>
    </div>
  );
}
