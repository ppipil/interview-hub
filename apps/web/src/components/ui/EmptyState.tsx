import type { ReactNode } from "react";

import { SurfaceCard } from "./SurfaceCard";

interface EmptyStateProps {
  title: string;
  description: string;
  action?: ReactNode;
}

export const EmptyState = ({ title, description, action }: EmptyStateProps) => (
  <SurfaceCard className="mx-auto max-w-2xl text-center">
    <div className="space-y-4">
      <h2 className="font-heading text-3xl font-extrabold tracking-tight text-slate-900">{title}</h2>
      <p className="text-sm leading-7 text-slate-500">{description}</p>
      {action ? <div className="flex justify-center">{action}</div> : null}
    </div>
  </SurfaceCard>
);
