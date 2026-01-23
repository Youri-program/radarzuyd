interface StatusPillProps {
  ok: boolean;
  label: string;
}

export const StatusPill: React.FC<StatusPillProps> = ({ ok, label }) => {
  return (
    <span className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-slate-900 text-xs">
      <span
        className={
          "w-2 h-2 rounded-full " + (ok ? "bg-emerald-400" : "bg-red-500")
        }
      />
      <span className="text-slate-100">{label}</span>
    </span>
  );
};
