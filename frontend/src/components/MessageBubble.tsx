import type { ChatMessage } from "../types/messages";
import { AgentStatusBadge } from "./AgentStatus";

interface Props {
  message: ChatMessage;
}

export function MessageBubble({ message }: Props) {
  const isCEO = message.role === "ceo";
  const isClarification = message.type === "clarification";

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: isCEO ? "flex-end" : "flex-start",
        marginBottom: "12px",
        animation: "fadeIn 0.3s ease",
      }}
    >
      {!isCEO && message.agent && (
        <div style={{ marginBottom: "4px" }}>
          <AgentStatusBadge agent={message.agent} status={message.agentStatus ?? "complete"} />
        </div>
      )}
      <div
        style={{
          maxWidth: "75%",
          padding: isClarification ? "14px 16px" : "10px 14px",
          borderRadius: isCEO ? "14px 14px 4px 14px" : "14px 14px 14px 4px",
          background: isCEO
            ? "linear-gradient(135deg, #4a9eff, #3a7bd5)"
            : isClarification
              ? "rgba(245,166,35,0.12)"
              : "rgba(255,255,255,0.06)",
          border: isClarification ? "1px solid rgba(245,166,35,0.25)" : "none",
          color: isCEO ? "#fff" : "#e0e0e8",
          fontSize: "14px",
          lineHeight: "1.55",
          whiteSpace: "pre-wrap",
          wordBreak: "break-word",
        }}
      >
        {isClarification && (
          <div
            style={{
              fontSize: "11px",
              fontWeight: 600,
              color: "#f5a623",
              marginBottom: "6px",
              textTransform: "uppercase",
              letterSpacing: "0.05em",
            }}
          >
            Need your input
          </div>
        )}
        {message.content}
      </div>
      <span
        style={{
          fontSize: "10px",
          color: "rgba(255,255,255,0.2)",
          marginTop: "3px",
          paddingLeft: isCEO ? "0" : "4px",
          paddingRight: isCEO ? "4px" : "0",
        }}
      >
        {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
      </span>
    </div>
  );
}
