import { ArrowLeft, RotateCcw } from "lucide-react";

import { Button } from "../../ui/Button";
import { SurfaceCard } from "../../ui/SurfaceCard";

interface RetryChallengePanelProps {
  onRetry: () => void;
  onHome: () => void;
}

export const RetryChallengePanel = ({ onRetry, onHome }: RetryChallengePanelProps) => (
  <SurfaceCard className="bg-gradient-to-br from-slate-900 via-slate-900 to-blue-900 text-white">
    <div className="space-y-5">
      <div className="space-y-3">
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-blue-200">Next Move</p>
        <h3 className="font-heading text-3xl font-extrabold tracking-tight">
          再来一轮，把这次的短板打穿。
        </h3>
        <p className="max-w-2xl text-sm leading-7 text-slate-300">
          真正让人进步的不是“看懂反馈”，而是把反馈立刻拿去下一轮试一遍。
        </p>
      </div>
      <div className="flex flex-col gap-3 sm:flex-row">
        <Button variant="primary" size="lg" onClick={onRetry} icon={<RotateCcw className="h-4 w-4" />}>
          再来一轮
        </Button>
        <Button variant="secondary" size="lg" onClick={onHome} icon={<ArrowLeft className="h-4 w-4" />}>
          回到首页
        </Button>
      </div>
    </div>
  </SurfaceCard>
);
