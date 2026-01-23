type Page = "live" | "history";

interface SidebarProps {
  currentPage: Page;
  onNavigate: (page: Page) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentPage, onNavigate }) => {
  const linkClasses = (active: boolean) =>
    [
      "flex items-center gap-2 px-4 py-2 rounded-md cursor-pointer text-sm transition-colors",
      active
        ? "bg-slate-800 text-white"
        : "text-slate-300 hover:bg-slate-800/60 hover:text-white",
    ].join(" ");

  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-950/90 flex flex-col">
      <div className="p-4 border-b border-slate-800">
        {/* Removed MA03 AIOps + description */}
      </div>

      <nav className="flex-1 p-4 space-y-1">
        <div
          className={linkClasses(currentPage === "live")}
          onClick={() => onNavigate("live")}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
          <span>Live View</span>
        </div>
        <div
          className={linkClasses(currentPage === "history")}
          onClick={() => onNavigate("history")}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
          <span>History</span>
        </div>
      </nav>

      <div className="p-4 border-t border-slate-800 text-[11px] text-slate-500">
        {/* Empty footer or add project info if needed */}
      </div>
    </aside>
  );
};
