"use client";

import { CheckIcon } from "@/components/icons/erp/generated/check";
import {
  FINANCE_CREATION_STEP_DEFS,
  useFinanceCreationFlow,
} from "@/features/college-admin/context/finance-creation-flow-context";
import { cn } from "@/lib/utils";

type Props = {
  activeIndex: number;
};

export function FinanceWorkflowStepper({ activeIndex }: Props) {
  const flow = useFinanceCreationFlow();

  return (
    <ol className="flex flex-wrap items-start gap-2 border-b border-[#e8ecf2] pb-5">
      {FINANCE_CREATION_STEP_DEFS.map((step, index) => {
        const isDone = index < activeIndex;
        const isActive = index === activeIndex;
        return (
          <li key={step.key} className="flex min-w-[5.5rem] flex-1 flex-col items-center gap-1.5 text-center">
            <button
              type="button"
              onClick={() => flow.goToStep(index)}
              className="flex flex-col items-center gap-1.5"
              aria-current={isActive ? "step" : undefined}
            >
              <span
                className={cn(
                  "flex size-7 items-center justify-center rounded-full border text-[11px] font-semibold",
                  isDone
                    ? "border-[#245dd8] bg-[#245dd8] text-white"
                    : isActive
                      ? "border-[#245dd8] text-[#245dd8]"
                      : "border-[#e5e7eb] text-[#9ca3af]",
                )}
              >
                {isDone ? <CheckIcon className="size-3.5" aria-hidden /> : index + 1}
              </span>
              <span
                className={cn(
                  "text-[11px] font-medium leading-tight",
                  isActive ? "text-[#245dd8]" : isDone ? "text-[#111827]" : "text-[#9ca3af]",
                )}
              >
                {step.label}
              </span>
            </button>
          </li>
        );
      })}
    </ol>
  );
}