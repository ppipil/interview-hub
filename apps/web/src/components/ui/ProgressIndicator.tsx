interface ProgressIndicatorProps {
  current: number;
  total: number;
  label?: string;
}

export const ProgressIndicator = ({ current, total, label }: ProgressIndicatorProps) => {
  const safeTotal = Math.max(total, 1);
  const percentage = `${Math.min(100, Math.max(0, (current / safeTotal) * 100))}%`;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-3 text-sm">
        <span className="font-semibold text-slate-500">{label ?? "当前进度"}</span>
        <span className="font-semibold text-slate-900">
          {current} / {total}
        </span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-slate-200">
        <div className="h-full rounded-full bg-brand-gradient" style={{ width: percentage }} />
      </div>
    </div>
  );
};
