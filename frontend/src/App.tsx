import { useState } from "react";
import { Chat } from "./components/Chat";
import { Dashboard } from "./components/Dashboard";

export function App() {
  const [showDashboard, setShowDashboard] = useState(false);

  return (
    <>
      <Chat
        onOpenDashboard={() => setShowDashboard(true)}
      />
      {showDashboard && (
        <Dashboard
          onClose={() => setShowDashboard(false)}
          onSelectSession={(id) => {
            setShowDashboard(false);
            // TODO: load session by ID
          }}
        />
      )}
    </>
  );
}
