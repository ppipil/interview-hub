import type { ReactNode } from "react";

import { cn } from "../../lib/cn";

interface PillProps {
  children: ReactNode;
  variant?: "brand" | "neutral" | "success" | "danger";
  className?: string;
}

const variantStyles = {
  brand: "bg-blue-50 text-blue-700",
  neutral: "bg-slate-100 text-slate-600",
  success: "bg-emerald-50 text-emerald-700",
  danger: "bg-red-50 text-red-700",
};

export const Pill = ({ children, variant = "neutral", className }: PillProps) => (
  <span
    className={cn(
      "inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold tracking-wide",
      variantStyles[variant],
      className,
    )}
  >
    {children}
  </span>
);
