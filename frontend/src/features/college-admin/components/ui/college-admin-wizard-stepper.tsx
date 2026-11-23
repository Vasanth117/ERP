"use client";

import { CheckIcon } from "@/components/icons/erp/generated/check";
import { collegeAdminPanelShellClass } from "@/features/college-admin/components/ui/dashboard-panel-ui";
import { cn } from "@/lib/utils";

export function CollegeAdminWizardStepper({
  steps,
  activeKey,
}: {
  steps: { key: string; label: string; step_number: number; status: string }[];
  activeKey: string;
}) {
  return (
    <section className={cn(collegeAdminPanelShellClass, "px-4 py-4 sm:px-6")}>
      <div className="flex flex-wrap items-center gap-y-3 sm:flex-nowrap">
        {steps.map((wizardStep, index) => {
          const active = wizardStep.key === activeKey;
          const done = wizardStep.status === "done";
          return (
            <div key={wizardStep.key} className="flex min-w-0 flex-1 items-center last:flex-none">
              <span
                className={cn(
                  "flex size-8 shrink-0 items-center justify-center rounded-full text-[13px] font-semibold tabular-nums",
                  active && "border-2 border-[#245dd8] bg-white text-[#245dd8]",
                  !active && !done && "border border-[#e5e7eb] bg-[#f9fafb] text-[#9ca3af]",
                  done && "border-2 border-[#245dd8] bg-[#245dd8] text-white",
                )}
              >
                {done ? <CheckIcon className="size-3.5" strokeWidth={2.5} aria-hidden /> : wizardStep.step_number}
              </span>
              <span
                className={cn(
                  "ml-2 hidden truncate text-[12px] sm:inline sm:text-[13px]",
                  active ? "font-semibold text-[#111827]" : "font-medium text-[#9ca3af]",
                )}
              >
                {wizardStep.label}
              </span>
              {index < steps.length -  1 ? (
                <div className="mx-2 hidden h-px min-w-[1rem] flex-1 bg-[#e5e7eb] sm:block" aria-hidden />
              ) : null}
            </div>
          );
        })}
      </div>
    </section>
  );
}