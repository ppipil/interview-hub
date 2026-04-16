import type { InterviewFeedback } from "../../../types";
import { Pill } from "../../ui/Pill";
import { SurfaceCard } from "../../ui/SurfaceCard";

interface SuggestedAnswerPanelProps {
  feedback: InterviewFeedback;
}

export const SuggestedAnswerPanel = ({ feedback }: SuggestedAnswerPanelProps) => (
  <SurfaceCard className="space-y-4">
    <Pill variant="brand">推荐回答方向</Pill>
    <h3 className="font-heading text-2xl font-extrabold tracking-tight text-slate-900">
      如果这一题重打一遍，可以这样收口
    </h3>
    <div className="rounded-2xl bg-slate-100/80 p-5">
      <p className="text-sm leading-8 text-slate-700">{feedback.suggestedAnswer}</p>
    </div>
  </SurfaceCard>
);
