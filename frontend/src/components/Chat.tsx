import { useCallback, useEffect, useRef, useState } from "react";
import type { ChatMessage } from "../types/messages";
import { useWebSocket } from "../hooks/useWebSocket";
import { MessageBubble } from "./MessageBubble";
import { AgentPipeline } from "./AgentPipeline";

let messageId = 0;

interface ChatProps {
  onOpenDashboard?: () => void;
}

export function Chat({ onOpenDashboard }: ChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [isProcessing, setIsProcessing] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [activeAgents, setActiveAgents] = useState<Map<string, string>>(new Map());
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const wsUrl =
    typeof window !== "undefined"
      ? `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}/api/chat`
      : "ws://localhost:8000/api/chat";

  const { send, lastMessage, connected } = useWebSocket(wsUrl);

  // Handle incoming messages
  useEffect(() => {
    if (!lastMessage) return;

    if (lastMessage.metadata?.session_id) {
      setSessionId(lastMessage.metadata.session_id as string);
    }

    // Track active agents
    if (lastMessage.type === "agent_status" && lastMessage.agent) {
      setActiveAgents((prev) => {
        const next = new Map(prev);
        if (lastMessage.agent_status === "complete") {
          next.delete(lastMessage.agent!);
        } else {
          next.set(lastMessage.agent!, lastMessage.agent_status ?? "working");
        }
        return next;
      });
    }

    // Handle preview URLs
    if (lastMessage.type === "preview" && lastMessage.metadata?.url) {
      setPreviewUrl(lastMessage.metadata.url as string);
    }

    // Done signal
    if (lastMessage.type === "done") {
      setIsProcessing(false);
      setActiveAgents(new Map());
    }

    // Add visible messages to chat
    if (lastMessage.content) {
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
    }
  }, [lastMessage]);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Focus input on load
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSend = useCallback(() => {
    const trimmed = input.trim();
    if (!trimmed || !connected) return;

    const msg: ChatMessage = {
      id: `ceo-${++messageId}`,
      role: "ceo",
      content: trimmed,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, msg]);
    setIsProcessing(true);
    send(trimmed, sessionId);
    setInput("");
  }, [input, send, sessionId, connected]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend]
  );

  // Auto-resize textarea
  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    const el = e.target;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 150) + "px";
  }, []);

  return (
    <div style={{ display: "flex", height: "100vh" }}>
      {/* Main chat area */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          flex: 1,
          maxWidth: previewUrl ? "50%" : "800px",
          margin: previewUrl ? "0" : "0 auto",
          padding: "0 16px",
        }}
      >
        {/* Header */}
        <header
          style={{
            padding: "16px 0",
            borderBottom: "1px solid rgba(255,255,255,0.08)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div>
            <h1 style={{ fontSize: "18px", fontWeight: 600, letterSpacing: "-0.02em" }}>
              MakeItHappen
            </h1>
            <p style={{ fontSize: "12px", color: "rgba(255,255,255,0.35)", marginTop: "2px" }}>
              As you wish, CEO
            </p>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            {onOpenDashboard && (
              <button
                onClick={onOpenDashboard}
                style={{
                  background: "rgba(255,255,255,0.06)",
                  border: "1px solid rgba(255,255,255,0.1)",
                  color: "rgba(255,255,255,0.5)",
                  padding: "5px 12px",
                  borderRadius: "6px",
                  cursor: "pointer",
                  fontSize: "12px",
                }}
              >
                Dashboard
              </button>
            )}
            <span
              style={{
                width: "8px",
                height: "8px",
                borderRadius: "50%",
                background: connected ? "#2ecc71" : "#e74c3c",
                display: "inline-block",
              }}
            />
            <span style={{ fontSize: "12px", color: "rgba(255,255,255,0.4)" }}>
              {connected ? "Ready" : "Connecting..."}
            </span>
          </div>
        </header>

        {/* Agent Pipeline Status */}
        {activeAgents.size > 0 && <AgentPipeline agents={activeAgents} />}

        {/* Messages */}
        <div style={{ flex: 1, overflowY: "auto", padding: "16px 0" }}>
          {messages.length === 0 && (
            <div
              style={{
                textAlign: "center",
                color: "rgba(255,255,255,0.2)",
                marginTop: "25vh",
              }}
            >
              <p style={{ fontSize: "32px", fontWeight: 200, letterSpacing: "-0.03em" }}>
                What would you like to build?
              </p>
              <p style={{ fontSize: "14px", marginTop: "12px", lineHeight: 1.6 }}>
                Tell me what you want. I'll handle the rest.
              </p>
              <div
                style={{
                  display: "flex",
                  gap: "8px",
                  justifyContent: "center",
                  marginTop: "24px",
                  flexWrap: "wrap",
                }}
              >
                {[
                  "Build me a landing page",
                  "Create a todo app",
                  "Set up a REST API",
                ].map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => {
                      setInput(suggestion);
                      inputRef.current?.focus();
                    }}
                    style={{
                      padding: "8px 14px",
                      borderRadius: "20px",
                      border: "1px solid rgba(255,255,255,0.1)",
                      background: "rgba(255,255,255,0.04)",
                      color: "rgba(255,255,255,0.5)",
                      fontSize: "13px",
                      cursor: "pointer",
                      transition: "all 0.2s",
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.borderColor = "rgba(74,158,255,0.4)";
                      e.currentTarget.style.color = "rgba(255,255,255,0.8)";
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderColor = "rgba(255,255,255,0.1)";
                      e.currentTarget.style.color = "rgba(255,255,255,0.5)";
                    }}
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}
          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}
          {isProcessing && messages.length > 0 && (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                padding: "8px 0",
                color: "rgba(255,255,255,0.3)",
                fontSize: "13px",
              }}
            >
              <span className="pulse-dot" />
              Working on it...
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div
          style={{
            padding: "12px 0 16px",
            borderTop: "1px solid rgba(255,255,255,0.08)",
          }}
        >
          <div style={{ display: "flex", gap: "8px", alignItems: "flex-end" }}>
            <textarea
              ref={inputRef}
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder={isProcessing ? "Working on your request..." : "Tell me what you need..."}
              disabled={isProcessing}
              rows={1}
              style={{
                flex: 1,
                padding: "10px 14px",
                borderRadius: "12px",
                border: "1px solid rgba(255,255,255,0.1)",
                background: isProcessing ? "rgba(255,255,255,0.02)" : "rgba(255,255,255,0.06)",
                color: "#e0e0e8",
                fontSize: "14px",
                resize: "none",
                outline: "none",
                fontFamily: "inherit",
                lineHeight: "1.4",
                transition: "border-color 0.2s",
              }}
              onFocus={(e) => (e.target.style.borderColor = "rgba(74,158,255,0.4)")}
              onBlur={(e) => (e.target.style.borderColor = "rgba(255,255,255,0.1)")}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || !connected || isProcessing}
              style={{
                padding: "10px 18px",
                borderRadius: "12px",
                border: "none",
                background:
                  input.trim() && connected && !isProcessing
                    ? "linear-gradient(135deg, #4a9eff, #3a7bd5)"
                    : "rgba(255,255,255,0.04)",
                color:
                  input.trim() && connected && !isProcessing
                    ? "#fff"
                    : "rgba(255,255,255,0.2)",
                fontSize: "14px",
                fontWeight: 600,
                cursor:
                  input.trim() && connected && !isProcessing
                    ? "pointer"
                    : "default",
                transition: "all 0.2s",
              }}
            >
              Go
            </button>
          </div>
          <p
            style={{
              fontSize: "11px",
              color: "rgba(255,255,255,0.2)",
              marginTop: "6px",
              textAlign: "center",
            }}
          >
            Enter to send &middot; Shift+Enter for new line &middot; Say "show me more" for details
          </p>
        </div>
      </div>

      {/* Preview Pane */}
      {previewUrl && (
        <div
          style={{
            flex: 1,
            borderLeft: "1px solid rgba(255,255,255,0.08)",
            display: "flex",
            flexDirection: "column",
          }}
        >
          <div
            style={{
              padding: "12px 16px",
              borderBottom: "1px solid rgba(255,255,255,0.08)",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <span style={{ fontSize: "13px", color: "rgba(255,255,255,0.5)" }}>
              Preview
            </span>
            <button
              onClick={() => setPreviewUrl(null)}
              style={{
                background: "none",
                border: "none",
                color: "rgba(255,255,255,0.4)",
                cursor: "pointer",
                fontSize: "16px",
              }}
            >
              x
            </button>
          </div>
          <iframe
            src={previewUrl}
            style={{
              flex: 1,
              border: "none",
              background: "#fff",
            }}
            title="Preview"
          />
        </div>
      )}
    </div>
  );
}
