import { ClipboardList } from "lucide-react";

import { AppShell } from "../components/ui/AppShell";
import { HeroEntry } from "../components/features/home/HeroEntry";
import { useInterviewStore } from "../store/useInterviewStore";
import { navigateToPath } from "../lib/navigation";

export const HomePage = () => {
  const setStage = useInterviewStore((state) => state.setStage);
  const openQuestionnaire = () => {
    navigateToPath("/interviewer-questionnaire");
  };

  return (
    <AppShell stage="home" className="flex min-h-[calc(100vh-92px)] items-center justify-center">
      <HeroEntry onStart={() => setStage("setup")} />
      <button
        aria-label="打开面试官问卷"
        className="group fixed bottom-5 right-5 z-30 flex h-14 items-center gap-3 rounded-2xl border border-slate-950/10 bg-slate-950 px-4 text-white shadow-2xl shadow-slate-950/25 transition hover:-translate-y-1 hover:bg-slate-900 sm:bottom-7 sm:right-7"
        onClick={openQuestionnaire}
        title="面试官问卷"
        type="button"
      >
        <ClipboardList className="h-5 w-5" />
        <span className="hidden whitespace-nowrap text-sm font-black tracking-tight sm:inline-block sm:max-w-0 sm:overflow-hidden sm:opacity-0 sm:transition-all sm:duration-200 sm:group-hover:max-w-28 sm:group-hover:opacity-100">
          面试官问卷
        </span>
      </button>
    </AppShell>
  );
};
