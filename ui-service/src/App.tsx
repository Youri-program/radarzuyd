import { useState, useEffect } from "react";
import { Sidebar } from "./components/Sidebar";
import { TopBar } from "./components/TopBar";
import { LiveView } from "./pages/LiveView";      
import History from "./pages/History";        
import { Login } from "./pages/Login";           
import { isAuthenticated, logout } from "./services/auth";

type Page = "live" | "history";

function App() {
  const [page, setPage] = useState<Page>("live");
  const [authenticated, setAuthenticated] = useState(false);
  const [checkingAuth, setCheckingAuth] = useState(true);

  useEffect(() => {
    setAuthenticated(isAuthenticated());
    setCheckingAuth(false);
  }, []);

  const handleLoginSuccess = () => {
    setAuthenticated(true);
  };

  const handleLogout = () => {
    logout();
    setAuthenticated(false);
  };

  if (checkingAuth) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950 text-slate-100">
        <div className="w-8 h-8 border-4 border-slate-700 border-t-slate-400 rounded-full animate-spin"></div>
      </div>
    );
  }

  if (!authenticated) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="min-h-screen flex bg-slate-950 text-slate-100">
      <Sidebar currentPage={page} onNavigate={setPage} />

      <div className="flex-1 flex flex-col">
        <TopBar onLogout={handleLogout} />

        <main className="flex-1 p-6">
          {page === "live" && <LiveView />}
          {page === "history" && <History />}
        </main>

        <footer className="border-t border-slate-800 text-[11px] text-slate-500 py-2 px-6 flex justify-between">
          <span>Radar Monitoring Dashboard</span>
          <span>Frontend prototype — React + Tailwind</span>
        </footer>
      </div>
    </div>
  );
}

export default App;