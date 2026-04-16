import { AudioLines } from "lucide-react";

import type { Interviewer, Session } from "../../../types";
import { Button } from "../../ui/Button";

interface InterviewStageHeaderProps {
  session: Session;
  interviewer: Interviewer;
  onHome: () => void;
}

export const InterviewStageHeader = ({
  session,
  interviewer,
  onHome,
}: InterviewStageHeaderProps) => {
  const modeLabel = session.mode === "guided" ? "Guided Mode" : "Real Mode";
  const interviewerLabel =
    interviewer.type === "avatar" ? `${interviewer.name} (SecondMe)` : interviewer.name;

  return (
    <header className="border-b border-slate-200/70 bg-white">
      <div className="mx-auto flex w-full max-w-[1100px] items-center justify-between px-5 py-5 sm:px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-2xl bg-[#EEF0FF] text-[#4B41E1]">
            <AudioLines className="h-4.5 w-4.5" />
          </div>
          <div className="font-heading text-[1.5rem] font-extrabold tracking-[-0.04em] text-[#0F172A] sm:text-[1.65rem]">
            InterviewAI
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={onHome}>
            回到首页
          </Button>
          <div className="hidden text-right sm:block">
            <p className="text-[9px] font-bold uppercase tracking-[0.24em] text-[#6B7280]">
              {modeLabel}
            </p>
            <p className="text-[13px] font-semibold text-[#111827]">{interviewerLabel}</p>
          </div>
          <img
            src={interviewer.avatarUrl}
            alt={interviewer.name}
            className="h-12 w-12 rounded-2xl border-[3px] border-[#4B41E1]/20 object-cover"
          />
        </div>
      </div>
    </header>
  );
};
