import type { ConversationMessage } from "../../../types";

interface QuestionPanelProps {
  question: ConversationMessage;
  currentRound: number;
  totalRounds: number;
}

export const QuestionPanel = ({
  question,
  currentRound,
  totalRounds,
}: QuestionPanelProps) => (
  <section className="space-y-5">
    <div className="flex items-center gap-3">
      <span className="rounded-full bg-[#E2DFFF] px-3.5 py-1.5 text-[9px] font-bold uppercase tracking-[0.24em] text-[#4B41E1] sm:text-[10px]">
        {`第 ${String(currentRound).padStart(2, "0")} 题 / ${String(totalRounds).padStart(2, "0")}`}
      </span>
      <div className="h-[3px] flex-1 overflow-hidden rounded-full bg-[#E5E7EB]">
        <div
          className="h-full rounded-full bg-[#4B41E1] transition-[width] duration-300"
          style={{ width: `${Math.max(8, (currentRound / totalRounds) * 100)}%` }}
        />
      </div>
    </div>

    <h1 className="font-heading text-[1.68rem] font-extrabold leading-[1.18] tracking-[-0.04em] text-black sm:text-[2rem]">
      {question.content}
    </h1>
  </section>
);
