/**
 * AgentPipeline — visual org chart showing which teams are active.
 * Gives the CEO a birds-eye view of who's working on their request.
 */

const AGENT_CONFIG: Record<string, { label: string; icon: string }> = {
  chief_of_staff: { label: "Chief of Staff", icon: "C" },
  product_owner: { label: "Product", icon: "P" },
  designer: { label: "Design", icon: "D" },
  engineer: { label: "Engineering", icon: "E" },
  qa: { label: "QA", icon: "Q" },
  devops: { label: "DevOps", icon: "O" },
};

const STATUS_COLORS: Record<string, string> = {
  thinking: "#f5a623",
  working: "#4a9eff",
  complete: "#2ecc71",
  blocked: "#e74c3c",
};

interface Props {
  agents: Map<string, string>;
}

export function AgentPipeline({ agents }: Props) {
  return (
    <div
      style={{
        display: "flex",
        gap: "6px",
        padding: "10px 0",
        borderBottom: "1px solid rgba(255,255,255,0.06)",
        overflowX: "auto",
      }}
    >
      {Array.from(agents.entries()).map(([agent, status]) => {
        const config = AGENT_CONFIG[agent] ?? { label: agent, icon: "?" };
        const color = STATUS_COLORS[status] ?? "#4a9eff";

        return (
          <div
            key={agent}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              padding: "6px 10px",
              borderRadius: "8px",
              background: `${color}15`,
              border: `1px solid ${color}30`,
              fontSize: "12px",
              color,
              whiteSpace: "nowrap",
              animation: status === "working" || status === "thinking" ? "pulse 2s infinite" : "none",
            }}
          >
            <span
              style={{
                width: "18px",
                height: "18px",
                borderRadius: "50%",
                background: `${color}25`,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "10px",
                fontWeight: 700,
              }}
            >
              {config.icon}
            </span>
            {config.label}
          </div>
        );
      })}
    </div>
  );
}
