import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "../../lib/cn";

interface SurfaceCardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  tone?: "default" | "muted" | "success" | "danger" | "dark";
}

const toneStyles = {
  default: "bg-white text-slate-900 shadow-panel",
  muted: "bg-slate-100/80 text-slate-900",
  success: "bg-emerald-50 text-slate-900",
  danger: "bg-red-50 text-slate-900",
  dark: "bg-slate-900 text-white shadow-float",
};

export const SurfaceCard = ({
  children,
  className,
  tone = "default",
  ...props
}: SurfaceCardProps) => (
  <div
    className={cn(
      "rounded-3xl p-6 ring-1 ring-slate-200/70",
      toneStyles[tone],
      className,
    )}
    {...props}
  >
    {children}
  </div>
);
