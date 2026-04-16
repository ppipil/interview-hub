import { ArrowUpRight } from "lucide-react";

import type { Interviewer } from "../../../types";
import { Button } from "../../ui/Button";
import { Pill } from "../../ui/Pill";
import { SectionTitle } from "../../ui/SectionTitle";
import { SurfaceCard } from "../../ui/SurfaceCard";

interface AvatarShowcaseProps {
  interviewers: Interviewer[];
  onQuickSelect: (interviewerId: string) => void;
}

export const AvatarShowcase = ({ interviewers, onQuickSelect }: AvatarShowcaseProps) => (
  <section className="space-y-6">
    <SectionTitle
      eyebrow="Featured Opponents"
      title="翻牌你的面试官"
      description="系统面试官负责稳准狠，AI 分身更像带风格的人。挑一个最让你紧张的，练起来才有感觉。"
    />
    <div className="grid gap-4 md:grid-cols-3">
      {interviewers.slice(0, 3).map((interviewer, index) => (
        <SurfaceCard
          key={interviewer.id}
          className={index === 1 ? "md:translate-y-8" : ""}
        >
          <div className="space-y-4">
            <div className="relative overflow-hidden rounded-2xl">
              <img
                src={interviewer.avatarUrl}
                alt={interviewer.name}
                className="h-72 w-full object-cover"
              />
              <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-slate-950/85 to-transparent p-5">
                <Pill variant={interviewer.type === "avatar" ? "brand" : "neutral"}>
                  {interviewer.type === "avatar" ? "SecondMe 分身" : "系统面试官"}
                </Pill>
                <h3 className="mt-3 font-heading text-2xl font-bold text-white">{interviewer.name}</h3>
                <p className="mt-1 text-sm text-slate-200">{interviewer.title}</p>
              </div>
            </div>
            <p className="text-sm leading-7 text-slate-500">{interviewer.description}</p>
            <Button
              variant="secondary"
              fullWidth
              onClick={() => onQuickSelect(interviewer.id)}
              icon={<ArrowUpRight className="h-4 w-4" />}
            >
              就从 TA 开练
            </Button>
          </div>
        </SurfaceCard>
      ))}
    </div>
  </section>
);
