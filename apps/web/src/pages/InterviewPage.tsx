import { EmptyState } from "../components/ui/EmptyState";
import { Button } from "../components/ui/Button";
import { AnswerComposer } from "../components/features/interview/AnswerComposer";
import { InterviewStageHeader } from "../components/features/interview/InterviewStageHeader";
import { QuestionPanel } from "../components/features/interview/QuestionPanel";
import { useInterviewStore } from "../store/useInterviewStore";

export const InterviewPage = () => {
  const session = useInterviewStore((state) => state.session);
  const interviewer = useInterviewStore((state) => state.activeInterviewer);
  const messages = useInterviewStore((state) => state.messages);
  const submitAnswer = useInterviewStore((state) => state.submitAnswer);
  const sendMessageStatus = useInterviewStore((state) => state.sendMessageStatus);
  const sendMessageError = useInterviewStore((state) => state.sendMessageError);
  const resetAll = useInterviewStore((state) => state.resetAll);
  const setStage = useInterviewStore((state) => state.setStage);

  const currentQuestion = [...messages].reverse().find((message) => message.role === "assistant");

  if (!session || !interviewer || !currentQuestion) {
    return (
      <div className="min-h-screen bg-[#F7F9FB] px-6 py-16">
        <EmptyState
          title="当前还没有激活中的面试"
          description="先回到配置页，选好岗位、模式和面试官，再开一轮正式挑战。"
          action={
            <Button onClick={() => setStage("setup")}>回到配置页</Button>
          }
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F7F9FB] text-[#191C1E]">
      <InterviewStageHeader session={session} interviewer={interviewer} onHome={resetAll} />

      <main className="mx-auto w-full max-w-[760px] px-5 pb-20 pt-8 sm:px-6 sm:pt-10">
        <div className="space-y-10">
          <QuestionPanel
            question={currentQuestion}
            mode={session.mode}
            role={session.role}
            currentRound={session.currentRound}
            totalRounds={session.totalRounds}
          />
          <AnswerComposer
            isSubmitting={sendMessageStatus === "loading"}
            error={sendMessageError}
            onSubmit={async (content) => {
              const response = await submitAnswer(content);
              return Boolean(response);
            }}
            onSkip={async () => {
              await submitAnswer("这道题我先跳过，请继续下一题。");
            }}
          />
        </div>
      </main>
    </div>
  );
};
