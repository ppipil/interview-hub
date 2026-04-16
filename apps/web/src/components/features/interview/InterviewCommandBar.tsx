import { PauseCircle, Volume2, LogOut } from "lucide-react";

interface InterviewCommandBarProps {
  isPaused: boolean;
  onTogglePause: () => void;
  onToggleAudio: () => void;
  onEndSession: () => void;
}

export const InterviewCommandBar = ({
  isPaused,
  onTogglePause,
  onToggleAudio,
  onEndSession,
}: InterviewCommandBarProps) => (
  <div className="fixed bottom-6 left-1/2 z-40 w-[calc(100%-28px)] max-w-[620px] -translate-x-1/2 rounded-[1.8rem] border border-white/70 bg-white/82 px-4 py-4 shadow-[0_24px_60px_rgba(15,23,42,0.12)] backdrop-blur-xl">
    <div className="grid grid-cols-3 divide-x divide-[#E0E3E5]">
      <button
        type="button"
        onClick={onTogglePause}
        className={`flex items-center justify-center gap-3 px-3 py-2 text-left text-[#45464D] transition ${
          isPaused ? "text-[#4B41E1]" : "hover:text-[#4B41E1]"
        }`}
      >
        <PauseCircle className="h-6 w-6 shrink-0" />
        <span className="text-[11px] font-bold uppercase tracking-[0.18em]">Pause</span>
      </button>

      <button
        type="button"
        onClick={onToggleAudio}
        className="flex items-center justify-center gap-3 px-3 py-2 text-[#45464D] transition hover:text-[#4B41E1]"
      >
        <Volume2 className="h-6 w-6 shrink-0" />
        <span className="text-[11px] font-bold uppercase tracking-[0.18em]">Audio</span>
      </button>

      <button
        type="button"
        onClick={onEndSession}
        className="flex items-center justify-center gap-3 px-3 py-2 text-[#45464D] transition hover:text-[#BA1A1A]"
      >
        <LogOut className="h-6 w-6 shrink-0" />
        <span className="text-[11px] font-bold uppercase tracking-[0.18em]">End Session</span>
      </button>
    </div>
  </div>
);
