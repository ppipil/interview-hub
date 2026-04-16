import { CheckCircle2 } from "lucide-react";

import { modeOptions } from "../../../config/interviewOptions";
import type { InterviewMode } from "../../../types";
import { SectionTitle } from "../../ui/SectionTitle";

interface ModeSelectorProps {
  selectedMode: InterviewMode | null;
  onSelect: (mode: InterviewMode) => void;
}

export const ModeSelector = ({ selectedMode, onSelect }: ModeSelectorProps) => (
  <section className="space-y-4">
    <SectionTitle title="选择模式" />
    <div className="space-y-2.5">
      {modeOptions.map((mode) => (
        <button
          key={mode.value}
          type="button"
          onClick={() => onSelect(mode.value)}
          className={`flex w-full items-center justify-between rounded-2xl border px-4 py-4 text-left transition active:scale-[0.98] ${
            selectedMode === mode.value
              ? "border-blue-600 bg-blue-600 text-white shadow-[0_18px_40px_-24px_rgba(37,99,235,0.9)]"
              : "border-slate-200 bg-white text-slate-900 hover:border-slate-300 hover:bg-slate-50"
          }`}
        >
          <span className="text-base font-semibold tracking-tight">{mode.label}</span>
          {selectedMode === mode.value ? <CheckCircle2 className="h-5 w-5 shrink-0" /> : null}
        </button>
      ))}
    </div>
  </section>
);
