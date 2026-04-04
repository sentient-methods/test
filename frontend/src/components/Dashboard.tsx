import { useCallback, useEffect, useState } from "react";

interface SessionInfo {
  id: string;
  created_at: string;
  message_count: number;
  last_intent: string;
  cost: {
    total_cost_usd: number;
    total_tokens: number;
    call_count: number;
    cost_by_agent: Record<string, number>;
  };
}

interface DashboardData {
  sessions: SessionInfo[];
  workspaces: { session_id: string; path: string; file_count: number }[];
  total_spend: number;
  session_count: number;
}

interface Props {
  onClose: () => void;
  onSelectSession: (sessionId: string) => void;
}

export function Dashboard({ onClose, onSelectSession }: Props) {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState<string | null>(null);

  const fetchDashboard = useCallback(async () => {
    try {
      const res = await fetch("/api/dashboard");
      const json = await res.json();
      setData(json);
    } catch (e) {
      console.error("Failed to load dashboard:", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  const handleDelete = useCallback(
    async (sessionId: string) => {
      if (!confirm("Remove this project and all its files?")) return;
      setDeleting(sessionId);
      try {
        await fetch(`/api/sessions/${sessionId}`, { method: "DELETE" });
        await fetchDashboard();
      } catch (e) {
        console.error("Delete failed:", e);
      } finally {
        setDeleting(null);
      }
    },
    [fetchDashboard]
  );

  if (loading) {
    return (
      <div style={{ padding: "40px", textAlign: "center", color: "rgba(255,255,255,0.4)" }}>
        Loading dashboard...
      </div>
    );
  }

  if (!data) return null;

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.85)",
        zIndex: 100,
        overflowY: "auto",
        padding: "20px",
      }}
    >
      <div style={{ maxWidth: "700px", margin: "0 auto" }}>
        {/* Header */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "24px",
          }}
        >
          <h2 style={{ fontSize: "18px", fontWeight: 600 }}>CEO Dashboard</h2>
          <button
            onClick={onClose}
            style={{
              background: "rgba(255,255,255,0.08)",
              border: "none",
              color: "#e0e0e8",
              padding: "6px 14px",
              borderRadius: "8px",
              cursor: "pointer",
              fontSize: "13px",
            }}
          >
            Close
          </button>
        </div>

        {/* Summary Cards */}
        <div style={{ display: "flex", gap: "12px", marginBottom: "24px", flexWrap: "wrap" }}>
          <StatCard label="Total Spend" value={`$${data.total_spend.toFixed(4)}`} />
          <StatCard label="Projects" value={String(data.session_count)} />
          <StatCard
            label="Files Created"
            value={String(data.workspaces.reduce((sum, w) => sum + w.file_count, 0))}
          />
        </div>

        {/* Sessions */}
        <h3 style={{ fontSize: "14px", color: "rgba(255,255,255,0.5)", marginBottom: "12px" }}>
          Projects
        </h3>
        {data.sessions.length === 0 ? (
          <p style={{ color: "rgba(255,255,255,0.3)", fontSize: "13px" }}>No projects yet.</p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {data.sessions.map((session) => {
              const workspace = data.workspaces.find((w) => w.session_id === session.id);
              return (
                <div
                  key={session.id}
                  style={{
                    background: "rgba(255,255,255,0.04)",
                    borderRadius: "10px",
                    padding: "14px 16px",
                    border: "1px solid rgba(255,255,255,0.06)",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
                    <div>
                      <div style={{ fontSize: "14px", fontWeight: 500, marginBottom: "4px" }}>
                        {session.last_intent || `Session ${session.id}`}
                      </div>
                      <div style={{ fontSize: "12px", color: "rgba(255,255,255,0.35)" }}>
                        {new Date(session.created_at).toLocaleDateString()} &middot;{" "}
                        {session.message_count} messages &middot;{" "}
                        {workspace?.file_count ?? 0} files &middot;{" "}
                        ${session.cost.total_cost_usd.toFixed(4)}
                      </div>
                      {Object.keys(session.cost.cost_by_agent).length > 0 && (
                        <div style={{ fontSize: "11px", color: "rgba(255,255,255,0.25)", marginTop: "4px" }}>
                          {Object.entries(session.cost.cost_by_agent)
                            .map(([agent, cost]) => `${agent}: $${cost.toFixed(4)}`)
                            .join(" | ")}
                        </div>
                      )}
                    </div>
                    <div style={{ display: "flex", gap: "6px" }}>
                      <button
                        onClick={() => onSelectSession(session.id)}
                        style={{
                          background: "rgba(74,158,255,0.15)",
                          border: "1px solid rgba(74,158,255,0.3)",
                          color: "#4a9eff",
                          padding: "4px 10px",
                          borderRadius: "6px",
                          cursor: "pointer",
                          fontSize: "12px",
                        }}
                      >
                        Open
                      </button>
                      <button
                        onClick={() => handleDelete(session.id)}
                        disabled={deleting === session.id}
                        style={{
                          background: "rgba(231,76,60,0.1)",
                          border: "1px solid rgba(231,76,60,0.25)",
                          color: "#e74c3c",
                          padding: "4px 10px",
                          borderRadius: "6px",
                          cursor: deleting === session.id ? "wait" : "pointer",
                          fontSize: "12px",
                          opacity: deleting === session.id ? 0.5 : 1,
                        }}
                      >
                        {deleting === session.id ? "..." : "Remove"}
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div
      style={{
        flex: "1 1 120px",
        background: "rgba(255,255,255,0.04)",
        borderRadius: "10px",
        padding: "14px 16px",
        border: "1px solid rgba(255,255,255,0.06)",
      }}
    >
      <div style={{ fontSize: "11px", color: "rgba(255,255,255,0.35)", marginBottom: "4px" }}>
        {label}
      </div>
      <div style={{ fontSize: "20px", fontWeight: 600 }}>{value}</div>
    </div>
  );
}
