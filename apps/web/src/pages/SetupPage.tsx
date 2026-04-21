import { useEffect } from "react";

import { AppShell } from "../components/ui/AppShell";
import { Button } from "../components/ui/Button";
import { ModeSelector } from "../components/features/setup/ModeSelector";
import { RoleSelector } from "../components/features/setup/RoleSelector";
import { InterviewerPicker } from "../components/features/setup/InterviewerPicker";
import { RoundSelector } from "../components/features/setup/RoundSelector";
import { SurfaceCard } from "../components/ui/SurfaceCard";
import { useInterviewStore, selectCanStartInterview } from "../store/useInterviewStore";

export const SetupPage = () => {
  const setup = useInterviewStore((state) => state.setup);
  const interviewers = useInterviewStore((state) => state.interviewers);
  const interviewersStatus = useInterviewStore((state) => state.interviewersStatus);
  const interviewersError = useInterviewStore((state) => state.interviewersError);
  const createSessionStatus = useInterviewStore((state) => state.createSessionStatus);
  const updateSetup = useInterviewStore((state) => state.updateSetup);
  const fetchInterviewers = useInterviewStore((state) => state.fetchInterviewers);
  const startInterview = useInterviewStore((state) => state.startInterview);
  const resetInterview = useInterviewStore((state) => state.resetInterview);
  const resetAll = useInterviewStore((state) => state.resetAll);
  const canStart = useInterviewStore(selectCanStartInterview);

  useEffect(() => {
    void fetchInterviewers(setup.role ?? undefined);
  }, [fetchInterviewers, setup.role]);

  return (
    <AppShell
      stage="setup"
      className="max-w-2xl pb-28"
      aside={
        <Button variant="ghost" onClick={resetAll}>
          回到首页
        </Button>
      }
    >
      <div className="space-y-8">
        <RoleSelector
          selectedRole={setup.role}
          onSelect={(role) => updateSetup({ role })}
        />
        <ModeSelector
          selectedMode={setup.mode}
          onSelect={(mode) => updateSetup({ mode })}
        />
        <RoundSelector
          selectedRounds={setup.totalRounds}
          onSelect={(totalRounds) => updateSetup({ totalRounds })}
        />
        <InterviewerPicker
          interviewers={interviewers}
          selectedInterviewerId={setup.interviewerId}
          isLoading={interviewersStatus === "loading"}
          error={interviewersError}
          onSelect={(interviewerId) => updateSetup({ interviewerId })}
        />

        <SurfaceCard className="sticky bottom-4 z-10 space-y-3 rounded-[2rem] border border-white/70 bg-white/90 p-4 backdrop-blur-xl">
          <Button
            fullWidth
            size="lg"
            onClick={() => {
              void startInterview();
            }}
            disabled={!canStart || createSessionStatus === "loading"}
          >
            {createSessionStatus === "loading" ? "正在拉起面试官..." : "开始挑战"}
          </Button>
          <Button fullWidth variant="ghost" onClick={resetInterview}>
            清空选择
          </Button>
        </SurfaceCard>
      </div>
    </AppShell>
  );
};
