interface SectionTitleProps {
  eyebrow?: string;
  title: string;
  description?: string;
}

export const SectionTitle = ({ eyebrow, title, description }: SectionTitleProps) => (
  <div className="space-y-2">
    {eyebrow ? (
      <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">{eyebrow}</p>
    ) : null}
    <h2 className="font-heading text-2xl font-extrabold tracking-tight text-slate-900">{title}</h2>
    {description ? <p className="max-w-2xl text-sm leading-6 text-slate-500">{description}</p> : null}
  </div>
);
