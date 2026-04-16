import type { ButtonHTMLAttributes, ReactNode } from "react";

import { cn } from "../../lib/cn";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost";
  size?: "sm" | "md" | "lg";
  icon?: ReactNode;
  fullWidth?: boolean;
}

const variantStyles = {
  primary:
    "bg-brand-gradient text-white shadow-panel hover:shadow-active hover:-translate-y-0.5",
  secondary:
    "bg-white text-slate-900 ring-1 ring-slate-200 hover:bg-slate-50 hover:ring-blue-200",
  ghost: "bg-transparent text-slate-600 hover:bg-white/70 hover:text-slate-900",
};

const sizeStyles = {
  sm: "px-4 py-2 text-sm",
  md: "px-5 py-3 text-sm",
  lg: "px-6 py-4 text-base",
};

export const Button = ({
  className,
  children,
  variant = "primary",
  size = "md",
  icon,
  fullWidth,
  ...props
}: ButtonProps) => (
  <button
    className={cn(
      "inline-flex items-center justify-center gap-2 rounded-full font-semibold transition duration-200 disabled:cursor-not-allowed disabled:opacity-50",
      variantStyles[variant],
      sizeStyles[size],
      fullWidth && "w-full",
      className,
    )}
    {...props}
  >
    {children}
    {icon}
  </button>
);
