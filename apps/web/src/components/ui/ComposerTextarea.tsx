import type { TextareaHTMLAttributes } from "react";

import { cn } from "../../lib/cn";

interface ComposerTextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label: string;
  helper?: string;
}

export const ComposerTextarea = ({
  label,
  helper,
  className,
  value,
  ...props
}: ComposerTextareaProps) => {
  const length = typeof value === "string" ? value.length : 0;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <label className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
          {label}
        </label>
        <span className="text-xs font-medium text-slate-400">{length} 字</span>
      </div>
      <textarea
        value={value}
        className={cn(
          "min-h-[180px] w-full rounded-3xl border border-slate-200 bg-white px-5 py-4 text-sm leading-7 text-slate-900 shadow-panel transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100",
          className,
        )}
        {...props}
      />
      {helper ? <p className="text-sm text-slate-500">{helper}</p> : null}
    </div>
  );
};
