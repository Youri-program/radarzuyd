import { getUsername } from "../services/auth";

interface TopBarProps {
  onLogout: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({ onLogout }) => {
  const username = getUsername();

  return (
    <header className="border-b border-slate-800 px-6 py-3 bg-slate-950/90 backdrop-blur">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold text-slate-100">
          Radar Detection Dashboard
        </h1>
        
        <div className="flex items-center gap-4">
          {username && (
            <span className="text-xs text-slate-400">
              {username}
            </span>
          )}
          
          <button
            onClick={onLogout}
            className="px-3 py-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-100 rounded-md transition-colors"
          >
            Logout
          </button>
        </div>
      </div>
    </header>
  );
};
