/** Message types matching the backend protocol. */

export type AgentPhase =
  | "chief_of_staff"
  | "product_owner"
  | "designer"
  | "engineer"
  | "qa"
  | "devops";

export type AgentStatus = "thinking" | "working" | "complete" | "blocked";

export interface SystemResponse {
  type: "message" | "agent_status" | "clarification" | "preview" | "done";
  content: string;
  agent: AgentPhase | null;
  agent_status: AgentStatus | null;
  metadata: Record<string, unknown>;
  timestamp: string;
}

export interface ChatMessage {
  id: string;
  role: "ceo" | "system";
  content: string;
  agent?: AgentPhase;
  agentStatus?: AgentStatus;
  type?: string;
  timestamp: Date;
}
