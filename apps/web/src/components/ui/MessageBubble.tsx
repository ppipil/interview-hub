import type { ConversationMessage, Interviewer } from "../../types";
import { cn } from "../../lib/cn";

interface MessageBubbleProps {
  message: ConversationMessage;
  interviewer?: Interviewer | null;
}

export const MessageBubble = ({ message, interviewer }: MessageBubbleProps) => {
  const isAssistant = message.role === "assistant";

  return (
    <div className={cn("flex w-full", isAssistant ? "justify-start" : "justify-end")}>
      <div
        className={cn(
          "max-w-[85%] rounded-3xl px-5 py-4 shadow-panel",
          isAssistant
            ? "bg-white text-slate-900 ring-1 ring-slate-200"
            : "bg-blue-600 text-white",
        )}
      >
        <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em]">
          <span className={cn(isAssistant ? "text-slate-500" : "text-blue-100")}>
            {isAssistant ? interviewer?.name ?? "AI 面试官" : "你"}
          </span>
        </div>
        <p className="text-sm leading-7">{message.content}</p>
      </div>
    </div>
  );
};
