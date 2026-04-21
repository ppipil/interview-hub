import { SectionTitle } from "../../ui/SectionTitle";

interface RoundSelectorProps {
  selectedRounds: number;
  onSelect: (rounds: number) => void;
}

const roundOptions = Array.from({ length: 10 }, (_, index) => index + 1);

export const RoundSelector = ({ selectedRounds, onSelect }: RoundSelectorProps) => (
  <section className="space-y-4">
    <SectionTitle title="选择轮次" />
    <div className="grid grid-cols-5 gap-2.5">
      {roundOptions.map((round) => {
        const selected = selectedRounds === round;
        return (
          <button
            key={round}
            type="button"
            onClick={() => onSelect(round)}
            className={`rounded-2xl border px-3 py-3 text-sm font-semibold transition active:scale-[0.98] ${
              selected
                ? "border-blue-600 bg-blue-600 text-white shadow-[0_18px_40px_-24px_rgba(37,99,235,0.9)]"
                : "border-slate-200 bg-white text-slate-900 hover:border-slate-300 hover:bg-slate-50"
            }`}
          >
            {round} 轮
          </button>
        );
      })}
    </div>
  </section>
);
