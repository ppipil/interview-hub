import { ArrowRight } from "lucide-react";

import { Button } from "../../ui/Button";

interface HeroEntryProps {
  onStart: () => void;
}

export const HeroEntry = ({ onStart }: HeroEntryProps) => (
  <section className="mx-auto flex w-full max-w-2xl flex-col items-center gap-8 text-center">
    <p className="max-w-xl text-balance font-heading text-4xl font-extrabold tracking-tight text-slate-900 md:text-5xl">
      开始一轮 AI 模拟面试。
    </p>
    <Button
      size="lg"
      onClick={onStart}
      icon={<ArrowRight className="h-4 w-4" />}
      className="min-w-[220px]"
    >
      开始挑战
    </Button>
  </section>
);
