import { AppShell } from "../components/ui/AppShell";
import { HeroEntry } from "../components/features/home/HeroEntry";
import { useInterviewStore } from "../store/useInterviewStore";

export const HomePage = () => {
  const setStage = useInterviewStore((state) => state.setStage);

  return (
    <AppShell stage="home" className="flex min-h-[calc(100vh-92px)] items-center justify-center">
      <HeroEntry onStart={() => setStage("setup")} />
    </AppShell>
  );
};
