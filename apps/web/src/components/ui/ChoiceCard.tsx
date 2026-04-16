import type { ReactNode } from "react";

import { Check } from "lucide-react";

import { cn } from "../../lib/cn";
import { Pill } from "./Pill";

interface ChoiceCardProps {
  title: string;
  description: string;
  badge?: string;
  icon?: ReactNode;
  selected?: boolean;
  tone?: "default" | "success" | "danger";
  onClick?: () => void;
}

const toneStyles = {
  default: "from-white to-slate-50",
  success: "from-emerald-50 to-white",
  danger: "from-red-50 to-white",
};

export const ChoiceCard = ({
  title,
  description,
  badge,
  icon,
  selected,
  tone = "default",
  onClick,
}: ChoiceCardProps) => (
  <button
    type="button"
    onClick={onClick}
    className={cn(
      "group flex w-full flex-col items-start gap-4 rounded-2xl border bg-gradient-to-br p-6 text-left transition duration-200",
      toneStyles[tone],
      selected
        ? "border-blue-500 shadow-active"
        : "border-transparent shadow-panel hover:-translate-y-0.5 hover:border-slate-200 hover:shadow-active",
    )}
  >
    <div className="flex w-full items-start justify-between gap-3">
      <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white text-blue-600 shadow-panel">
        {icon}
      </div>
      {selected ? (
        <span className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 text-white">
          <Check className="h-4 w-4" />
        </span>
      ) : null}
    </div>
    <div className="space-y-3">
      {badge ? <Pill variant="neutral">{badge}</Pill> : null}
      <div className="space-y-2">
        <h3 className="font-heading text-lg font-bold text-slate-900">{title}</h3>
        <p className="text-sm leading-6 text-slate-500">{description}</p>
      </div>
    </div>
  </button>
);
