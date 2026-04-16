import { CheckCircle2 } from "lucide-react";

import { roleOptions } from "../../../config/interviewOptions";
import type { InterviewRole } from "../../../types";
import { SectionTitle } from "../../ui/SectionTitle";

interface RoleSelectorProps {
  selectedRole: InterviewRole | null;
  onSelect: (role: InterviewRole) => void;
}

export const RoleSelector = ({ selectedRole, onSelect }: RoleSelectorProps) => (
  <section className="space-y-4">
    <SectionTitle title="选择岗位" />
    <div className="space-y-2.5">
      {roleOptions.map((role) => (
        <button
          key={role.value}
          type="button"
          onClick={() => onSelect(role.value)}
          className={`flex w-full items-center justify-between rounded-2xl border px-4 py-4 text-left transition active:scale-[0.98] ${
            selectedRole === role.value
              ? "border-blue-600 bg-blue-600 text-white shadow-[0_18px_40px_-24px_rgba(37,99,235,0.9)]"
              : "border-slate-200 bg-white text-slate-900 hover:border-slate-300 hover:bg-slate-50"
          }`}
        >
          <span className="text-base font-semibold tracking-tight">{role.label}</span>
          {selectedRole === role.value ? (
            <CheckCircle2 className="h-5 w-5 shrink-0" />
          ) : null}
        </button>
      ))}
    </div>
  </section>
);
