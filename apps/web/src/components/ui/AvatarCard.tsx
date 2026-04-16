import { CheckCircle2 } from "lucide-react";

import type { Interviewer } from "../../types";
import { cn } from "../../lib/cn";

interface AvatarCardProps {
  interviewer: Interviewer;
  selected?: boolean;
  onClick?: () => void;
}

export const AvatarCard = ({ interviewer, selected, onClick }: AvatarCardProps) => (
  <button
    type="button"
    onClick={onClick}
    className={cn(
      "flex w-full items-center gap-4 rounded-2xl border p-4 text-left transition duration-200",
      selected
        ? "border-blue-600 bg-blue-600 text-white shadow-[0_18px_40px_-24px_rgba(37,99,235,0.9)]"
        : "border-slate-200 bg-white text-slate-900 hover:border-slate-300 hover:bg-slate-50",
    )}
  >
    <img
      src={interviewer.avatarUrl}
      alt={interviewer.name}
      className="h-12 w-12 rounded-2xl object-cover"
    />
    <div className="min-w-0 flex-1">
      <p
        className={cn(
          "font-heading text-base font-bold tracking-tight",
          selected ? "text-white" : "text-slate-900",
        )}
      >
        {interviewer.name}
      </p>
    </div>
    {selected ? <CheckCircle2 className="h-5 w-5 shrink-0" /> : null}
  </button>
);
