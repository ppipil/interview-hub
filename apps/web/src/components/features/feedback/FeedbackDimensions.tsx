import type { InterviewFeedback } from "../../../types";
import { SurfaceCard } from "../../ui/SurfaceCard";

interface FeedbackDimensionsProps {
  feedback: InterviewFeedback;
}

export const FeedbackDimensions = ({ feedback }: FeedbackDimensionsProps) => (
  <section className="grid gap-4 md:grid-cols-3">
    {feedback.dimensions.map((dimension) => (
      <SurfaceCard key={dimension.key}>
        <div className="space-y-3">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
            {dimension.label}
          </p>
          <div className="flex items-end justify-between gap-4">
            <p className="font-heading text-4xl font-extrabold tracking-tight text-slate-900">
              {dimension.score}
            </p>
            <p className="text-sm text-slate-400">/ 5</p>
          </div>
          <p className="text-sm leading-7 text-slate-500">{dimension.comment}</p>
        </div>
      </SurfaceCard>
    ))}
  </section>
);
