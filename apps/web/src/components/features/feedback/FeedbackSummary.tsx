import { BarChart3 } from "lucide-react";

import type { InterviewFeedback } from "../../../types";
import { SurfaceCard } from "../../ui/SurfaceCard";

interface FeedbackSummaryProps {
  feedback: InterviewFeedback;
}

export const FeedbackSummary = ({ feedback }: FeedbackSummaryProps) => (
  <SurfaceCard className="rounded-[1.75rem] border border-slate-200/70 p-8 shadow-[0_10px_30px_rgba(15,23,42,0.04)]">
    <div className="flex items-start gap-4">
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-[#EEF0FF] text-[#4B41E1]">
        <BarChart3 className="h-6 w-6" />
      </div>
      <div className="space-y-2">
        <h2 className="font-heading text-[1.9rem] font-extrabold tracking-tight text-slate-900 sm:text-[2rem]">
          综合评价
        </h2>
        <p className="max-w-2xl text-sm leading-7 text-slate-700 sm:text-[0.95rem]">
          {feedback.summary}
        </p>
      </div>
    </div>
  </SurfaceCard>
);
