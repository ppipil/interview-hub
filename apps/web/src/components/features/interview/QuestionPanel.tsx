import { Lightbulb } from "lucide-react";

import type { ConversationMessage, InterviewMode, InterviewRole } from "../../../types";

interface QuestionPanelProps {
  question: ConversationMessage;
  mode: InterviewMode;
  role: InterviewRole;
  currentRound: number;
  totalRounds: number;
}

const guidedHints: Record<InterviewRole, string> = {
  frontend: "可以从状态边界、全局状态和服务端状态的拆分思路来回答。",
  backend: "可以从服务边界、链路瓶颈、缓存策略或异步处理来展开。",
  product_manager: "可以从问题定义、优先级、取舍逻辑和推进节奏来回答。",
  operations: "可以从渠道、转化漏斗、实验设计和业务结果来组织答案。",
  data_analyst: "可以从指标定义、分析框架和结论如何推动动作来回答。",
};

export const QuestionPanel = ({
  question,
  mode,
  role,
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

    {mode === "guided" ? (
      <div className="rounded-[1.35rem] border border-[#ECEEF0] bg-white px-4.5 py-3.5 shadow-[0_8px_30px_rgba(15,23,42,0.05)]">
        <div className="flex items-start gap-3.5">
          <div className="mt-0.5 flex h-9 w-9 items-center justify-center rounded-xl bg-[#EEF0FF] text-[#4B41E1]">
            <Lightbulb className="h-4 w-4" />
          </div>
          <div className="space-y-1.5">
            <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-[#45464D]">
              带飞提示
            </p>
            <p className="text-[0.88rem] leading-6 text-[#45464D]">{guidedHints[role]}</p>
          </div>
        </div>
      </div>
    ) : null}
  </section>
);
