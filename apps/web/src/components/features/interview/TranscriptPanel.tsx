import type { ConversationMessage, Interviewer } from "../../../types";
import { MessageBubble } from "../../ui/MessageBubble";
import { SectionTitle } from "../../ui/SectionTitle";
import { SurfaceCard } from "../../ui/SurfaceCard";

interface TranscriptPanelProps {
  messages: ConversationMessage[];
  interviewer: Interviewer;
}

export const TranscriptPanel = ({ messages, interviewer }: TranscriptPanelProps) => (
  <SurfaceCard className="space-y-5">
    <SectionTitle
      eyebrow="Transcript"
      title="对话记录"
      description="这里只在你需要回看时再展开，默认不打断当前答题节奏。"
    />
    <div className="space-y-4">
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} interviewer={interviewer} />
      ))}
    </div>
  </SurfaceCard>
);
