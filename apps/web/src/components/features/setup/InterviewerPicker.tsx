import type { Interviewer } from "../../../types";
import { AvatarCard } from "../../ui/AvatarCard";
import { SectionTitle } from "../../ui/SectionTitle";
import { SurfaceCard } from "../../ui/SurfaceCard";

interface InterviewerPickerProps {
  interviewers: Interviewer[];
  selectedInterviewerId: string | null;
  isLoading: boolean;
  error: string | null;
  onSelect: (interviewerId: string) => void;
}

export const InterviewerPicker = ({
  interviewers,
  selectedInterviewerId,
  isLoading,
  error,
  onSelect,
}: InterviewerPickerProps) => {
  const sortedInterviewers = [
    ...interviewers.filter((item) => item.type === "system"),
    ...interviewers.filter((item) => item.type === "avatar"),
  ];

  return (
    <section className="space-y-4">
      <SectionTitle title="选择面试官" />

      {error ? (
        <SurfaceCard tone="danger">
          <p className="text-sm leading-7 text-slate-700">{error}</p>
        </SurfaceCard>
      ) : null}

      {isLoading ? (
        <SurfaceCard className="animate-pulse">
          <div className="space-y-3">
            <div className="h-16 rounded-2xl bg-slate-100" />
            <div className="h-16 rounded-2xl bg-slate-100" />
            <div className="h-16 rounded-2xl bg-slate-100" />
          </div>
        </SurfaceCard>
      ) : null}

      {!isLoading ? (
        <div className="space-y-3">
          {sortedInterviewers.map((interviewer) => (
            <AvatarCard
              key={interviewer.id}
              interviewer={interviewer}
              selected={selectedInterviewerId === interviewer.id}
              onClick={() => onSelect(interviewer.id)}
            />
          ))}
        </div>
      ) : null}
    </section>
  );
};
