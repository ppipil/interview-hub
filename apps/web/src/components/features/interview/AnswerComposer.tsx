import { useState, type KeyboardEvent } from "react";
import { Mic, Play, TriangleAlert } from "lucide-react";

interface AnswerComposerProps {
  isSubmitting: boolean;
  error: string | null;
  onSubmit: (content: string) => Promise<boolean>;
  onSkip: () => Promise<void>;
}

const MAX_RESPONSE_LENGTH = 2000;

export const AnswerComposer = ({
  isSubmitting,
  error,
  onSubmit,
  onSkip,
}: AnswerComposerProps) => {
  const [value, setValue] = useState("");

  const handleSubmit = async () => {
    const trimmed = value.trim();

    if (!trimmed) {
      return;
    }

    const succeeded = await onSubmit(trimmed);

    if (succeeded) {
      setValue("");
    }
  };

  const handleKeyDown = async (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
      event.preventDefault();
      await handleSubmit();
    }
  };

  return (
    <section className="space-y-5">
      <div className="space-y-4">
        <label className="block px-2 text-[11px] font-bold uppercase tracking-[0.2em] text-[#45464D]">
          你的回答
        </label>
        <div className="relative">
          <textarea
            value={value}
            maxLength={MAX_RESPONSE_LENGTH}
            disabled={isSubmitting}
            placeholder="在这里输入你的回答..."
            onChange={(event) => setValue(event.target.value)}
            onKeyDown={handleKeyDown}
            className="min-h-[420px] w-full resize-none rounded-[1.45rem] border border-[#E0E3E5] bg-white px-7 py-8 font-body text-[0.92rem] leading-7 text-[#191C1E] shadow-[0_10px_30px_rgba(15,23,42,0.04)] placeholder:text-[#B8BDC7] focus:border-[#C6C6CD] focus:outline-none focus:ring-4 focus:ring-[#E2DFFF]/50 disabled:cursor-not-allowed disabled:bg-[#F2F4F6]"
          />
          <div className="pointer-events-none absolute bottom-5 right-6 flex items-center gap-3 text-[#76777D]">
            <Mic className="h-4.5 w-4.5" />
            <span className="h-5 w-px bg-[#E0E3E5]" />
            <span className="font-mono text-[12px]">{`${value.length} / ${MAX_RESPONSE_LENGTH}`}</span>
          </div>
        </div>

        {error ? (
          <div className="flex items-center gap-3 rounded-2xl border border-[#FECACA] bg-[#FEF2F2] px-4 py-3 text-[13px] text-[#991B1B]">
            <TriangleAlert className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        ) : null}
      </div>

      <div className="space-y-4">
        <button
          type="button"
          onClick={() => {
            void handleSubmit();
          }}
          disabled={isSubmitting || !value.trim()}
          className="flex w-full items-center justify-center gap-3 rounded-xl bg-gradient-to-br from-[#4B41E1] to-[#645EFB] px-8 py-4 text-[0.9rem] font-bold text-white shadow-[0_18px_30px_rgba(75,65,225,0.28)] transition active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
        >
          <span>{isSubmitting ? "提交中..." : "提交回答"}</span>
          <Play className="h-4 w-4 fill-current" />
        </button>

        <button
          type="button"
          onClick={() => {
            void onSkip();
          }}
          disabled={isSubmitting}
          className="w-full rounded-xl bg-[#ECEEF0] px-8 py-4 text-[0.9rem] font-bold text-black transition hover:bg-[#E6E8EA] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
        >
          跳过这题
        </button>
      </div>
    </section>
  );
};
