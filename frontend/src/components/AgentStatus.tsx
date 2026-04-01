import type { AgentPhase, AgentStatus as Status } from "../types/messages";

const AGENT_LABELS: Record<AgentPhase, string> = {
  chief_of_staff: "Chief of Staff",
  product_owner: "Product",
  designer: "Design",
  engineer: "Engineering",
  qa: "QA",
  devops: "DevOps",
};

const STATUS_INDICATORS: Record<Status, { icon: string; color: string }> = {
  thinking: { icon: "\u2022", color: "#f5a623" },
  working: { icon: "\u25B6", color: "#4a9eff" },
  complete: { icon: "\u2713", color: "#2ecc71" },
  blocked: { icon: "!", color: "#e74c3c" },
};

interface Props {
  agent: AgentPhase | null;
  status: Status | null;
}

export function AgentStatusBadge({ agent, status }: Props) {
  if (!agent || !status) return null;

  const label = AGENT_LABELS[agent] ?? agent;
  const indicator = STATUS_INDICATORS[status] ?? STATUS_INDICATORS.thinking;

  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "6px",
        padding: "4px 10px",
        borderRadius: "12px",
        background: "rgba(255,255,255,0.06)",
        fontSize: "12px",
        color: indicator.color,
        fontWeight: 500,
      }}
    >
      <span style={{ fontSize: "10px" }}>{indicator.icon}</span>
      {label}
    </span>
  );
}
