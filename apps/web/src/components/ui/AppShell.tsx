import type { ReactNode } from "react";

import { Sparkles } from "lucide-react";

import { stageLabels } from "../../config/interviewOptions";
import type { InterviewStage } from "../../types";
import { cn } from "../../lib/cn";
import { Pill } from "./Pill";

interface AppShellProps {
  stage: InterviewStage;
  children: ReactNode;
  aside?: ReactNode;
  className?: string;
}

export const AppShell = ({ stage, children, aside, className }: AppShellProps) => (
  <div className="relative min-h-screen overflow-hidden">
    <div className="pointer-events-none absolute inset-0 surface-grid opacity-50" />
    <div className="pointer-events-none absolute -left-16 top-20 h-48 w-48 rounded-full bg-blue-200/40 blur-3xl" />
    <div className="pointer-events-none absolute right-0 top-0 h-64 w-64 rounded-full bg-indigo-200/30 blur-3xl" />

    <header className="sticky top-0 z-20 border-b border-white/60 bg-white/70 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-brand-gradient text-white shadow-panel">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <p className="font-heading text-lg font-extrabold tracking-tight text-slate-900">
              Interview Hub
            </p>
            <p className="text-xs font-medium uppercase tracking-[0.2em] text-slate-500">
              {stageLabels[stage]}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Pill variant="brand">AI 模拟面试 MVP</Pill>
          {aside}
        </div>
      </div>
    </header>

    <main className={cn("relative z-10 mx-auto max-w-7xl px-6 py-10 md:py-14", className)}>
      {children}
    </main>
  </div>
);
