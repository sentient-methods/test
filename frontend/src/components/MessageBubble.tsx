import type { ChatMessage } from "../types/messages";
import { AgentStatusBadge } from "./AgentStatus";

interface Props {
  message: ChatMessage;
}

export function MessageBubble({ message }: Props) {
  const isCEO = message.role === "ceo";

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: isCEO ? "flex-end" : "flex-start",
        marginBottom: "16px",
      }}
    >
      {!isCEO && message.agent && (
        <AgentStatusBadge agent={message.agent} status={message.agentStatus ?? "complete"} />
      )}
      <div
        style={{
          maxWidth: "70%",
          padding: "12px 16px",
          borderRadius: isCEO ? "16px 16px 4px 16px" : "16px 16px 16px 4px",
          background: isCEO
            ? "linear-gradient(135deg, #4a9eff, #3a7bd5)"
            : "rgba(255,255,255,0.08)",
          color: isCEO ? "#fff" : "#e0e0e8",
          fontSize: "14px",
          lineHeight: "1.5",
          marginTop: "4px",
          whiteSpace: "pre-wrap",
        }}
      >
        {message.content}
      </div>
      <span
        style={{
          fontSize: "11px",
          color: "rgba(255,255,255,0.3)",
          marginTop: "4px",
        }}
      >
        {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
      </span>
    </div>
  );
}
