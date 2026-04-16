import { useEffect } from "react";
import { AudioLines } from "lucide-react";

import { EmptyState } from "../components/ui/EmptyState";
import { Button } from "../components/ui/Button";
import { SurfaceCard } from "../components/ui/SurfaceCard";
import { FeedbackSummary } from "../components/features/feedback/FeedbackSummary";
import { ImprovementChecklist } from "../components/features/feedback/ImprovementChecklist";
import { RoundReviewList } from "../components/features/feedback/RoundReviewList";
import { useInterviewStore } from "../store/useInterviewStore";

export const FeedbackPage = () => {
  const session = useInterviewStore((state) => state.session);
  const interviewer = useInterviewStore((state) => state.activeInterviewer);
  const feedback = useInterviewStore((state) => state.feedback);
  const feedbackStatus = useInterviewStore((state) => state.feedbackStatus);
  const feedbackError = useInterviewStore((state) => state.feedbackError);
  const fetchFeedback = useInterviewStore((state) => state.fetchFeedback);
  const resetInterview = useInterviewStore((state) => state.resetInterview);
  const resetAll = useInterviewStore((state) => state.resetAll);

  useEffect(() => {
    if (session && !feedback && feedbackStatus !== "loading") {
      void fetchFeedback();
    }
  }, [feedback, feedbackStatus, fetchFeedback, session]);

  if (!session) {
    return (
      <div className="min-h-screen bg-[#F7F9FB] px-6 py-16">
        <EmptyState
          title="这份战报还没生成"
          description="先完整走完一轮面试，对话结束后这里才会出现真正的复盘结果。"
          action={<Button onClick={resetInterview}>去配置下一轮</Button>}
        />
      </div>
    );
  }

  if (feedbackStatus === "loading" || !feedback) {
    return (
      <div className="min-h-screen bg-[#F7F9FB] px-6 py-16">
        <SurfaceCard className="mx-auto max-w-3xl animate-pulse rounded-[1.75rem] p-8">
          <div className="space-y-4">
            <div className="h-4 w-32 rounded-full bg-slate-200" />
            <div className="h-10 w-3/4 rounded-full bg-slate-100" />
            <div className="h-32 rounded-3xl bg-slate-100" />
          </div>
          {feedbackError ? <p className="mt-4 text-sm text-red-600">{feedbackError}</p> : null}
        </SurfaceCard>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F7F9FB] text-[#191C1E]">
      <header className="border-b border-slate-200/70 bg-white">
        <div className="mx-auto flex w-full max-w-[1100px] items-center justify-between px-5 py-6 sm:px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-[#EEF0FF] text-[#4B41E1]">
              <AudioLines className="h-5 w-5" />
            </div>
            <div className="font-heading text-[2rem] font-extrabold tracking-[-0.04em] text-[#0F172A]">
              InterviewAI
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Button variant="ghost" size="sm" onClick={resetAll}>
              回到首页
            </Button>
            {interviewer ? (
              <img
                src={interviewer.avatarUrl}
                alt={interviewer.name}
                className="h-12 w-12 rounded-2xl border-[3px] border-[#4B41E1]/20 object-cover"
              />
            ) : null}
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-[860px] px-5 py-12 sm:px-6">
        <div className="mb-12 text-center">
          <p className="text-xs font-bold uppercase tracking-[0.26em] text-slate-500">复盘报告</p>
          <h1 className="mt-4 font-heading text-[2.6rem] font-extrabold tracking-tight text-slate-900 sm:text-[3.2rem]">
            面试反馈
          </h1>
          <div className="mx-auto mt-5 h-1.5 w-24 rounded-full bg-gradient-to-r from-[#4B41E1] to-[#645EFB]" />
        </div>

        <div className="space-y-6">
          <FeedbackSummary feedback={feedback} />
          <ImprovementChecklist feedback={feedback} />
          <RoundReviewList roundReviews={feedback.roundReviews} />
        </div>
      </main>
    </div>
  );
};
