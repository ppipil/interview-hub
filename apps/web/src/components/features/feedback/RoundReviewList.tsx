import { useEffect, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

import type { RoundReview } from "../../../types";
import { SurfaceCard } from "../../ui/SurfaceCard";

interface RoundReviewListProps {
  roundReviews: RoundReview[];
}

export const RoundReviewList = ({ roundReviews }: RoundReviewListProps) => {
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    setActiveIndex((current) => Math.min(current, Math.max(roundReviews.length - 1, 0)));
  }, [roundReviews.length]);

  if (roundReviews.length === 0) {
    return null;
  }

  const currentIndex = Math.min(activeIndex, roundReviews.length - 1);
  const currentRound = roundReviews[currentIndex];

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.24em] text-slate-500">Round Review</p>
          <h2 className="mt-2 font-heading text-[1.9rem] font-extrabold tracking-tight text-slate-900 sm:text-[2rem]">
            每一轮回答复盘
          </h2>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setActiveIndex((index) => Math.max(index - 1, 0))}
            disabled={currentIndex === 0}
            className="flex h-10 w-10 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-600 transition hover:border-slate-300 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          <button
            type="button"
            onClick={() => setActiveIndex((index) => Math.min(index + 1, roundReviews.length - 1))}
            disabled={currentIndex === roundReviews.length - 1}
            className="flex h-10 w-10 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-600 transition hover:border-slate-300 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </div>

      <SurfaceCard className="space-y-5 rounded-[1.6rem] border border-slate-200/70 p-6 shadow-[0_10px_30px_rgba(15,23,42,0.04)]">
        <div className="flex items-center justify-between gap-3">
          <span className="rounded-full bg-[#E2DFFF] px-4 py-1.5 text-[11px] font-bold uppercase tracking-[0.2em] text-[#4B41E1]">
            {`第 ${String(currentRound.round).padStart(2, "0")} 轮`}
          </span>
          <p className="text-xs font-medium text-slate-500">
            {`${currentIndex + 1} / ${roundReviews.length}`}
          </p>
        </div>

        <div className="space-y-2">
          <p className="text-xs font-bold uppercase tracking-[0.22em] text-slate-500">问题</p>
          <p className="text-sm leading-7 text-slate-900 sm:text-[0.95rem]">{currentRound.question}</p>
        </div>

        <div className="space-y-2 rounded-[1.25rem] bg-slate-100/80 p-4">
          <p className="text-xs font-bold uppercase tracking-[0.22em] text-slate-500">你的回答</p>
          <p className="text-sm leading-7 text-slate-700 sm:text-[0.95rem]">
            {currentRound.answer || "这一轮没有作答记录。"}
          </p>
        </div>

        <div className="rounded-[1.1rem] border border-amber-200 bg-amber-50 px-4 py-3">
          <p className="text-xs font-bold uppercase tracking-[0.22em] text-amber-700">本轮评价</p>
          <p className="mt-2 text-sm leading-7 text-slate-800 sm:text-[0.95rem]">
            {currentRound.evaluation}
          </p>
        </div>

        <div className="rounded-[1.1rem] border border-emerald-200 bg-emerald-50 px-4 py-3">
          <p className="text-xs font-bold uppercase tracking-[0.22em] text-emerald-700">参考答案</p>
          <p className="mt-2 text-sm leading-7 text-slate-800 sm:text-[0.95rem]">
            {currentRound.referenceAnswer}
          </p>
        </div>

        <div className="flex justify-center gap-2">
          {roundReviews.map((item, index) => (
            <button
              key={item.round}
              type="button"
              onClick={() => setActiveIndex(index)}
              className={`h-2.5 rounded-full transition ${
                index === currentIndex ? "w-6 bg-[#4B41E1]" : "w-2.5 bg-slate-300 hover:bg-slate-400"
              }`}
              aria-label={`切换到第 ${item.round} 轮`}
            />
          ))}
        </div>
      </SurfaceCard>
    </section>
  );
};
