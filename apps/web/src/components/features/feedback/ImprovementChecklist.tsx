import type { InterviewFeedback } from "../../../types";
import { SurfaceCard } from "../../ui/SurfaceCard";

interface ImprovementChecklistProps {
  feedback: InterviewFeedback;
}

export const ImprovementChecklist = ({ feedback }: ImprovementChecklistProps) => (
  <SurfaceCard className="rounded-[1.75rem] border border-slate-200/70 bg-slate-50/80 p-8 shadow-[0_10px_30px_rgba(15,23,42,0.04)]">
    <div className="space-y-5">
      <h2 className="font-heading text-[1.9rem] font-extrabold tracking-tight text-slate-900 sm:text-[2rem]">
        改进建议
      </h2>
      <div className="space-y-4">
        {feedback.improvements.map((item) => (
          <div key={item} className="flex items-start gap-3">
            <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-[#4B41E1]" />
            <p className="text-sm leading-7 text-slate-700 sm:text-[0.95rem]">{item}</p>
          </div>
        ))}
      </div>
    </div>
  </SurfaceCard>
);
