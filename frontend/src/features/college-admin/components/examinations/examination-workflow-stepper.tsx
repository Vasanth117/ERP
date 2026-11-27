"use client";

import Link from "next/link";

import { CheckIcon } from "@/components/icons/erp/generated/check";
import type { ExaminationWorkflowStep } from "@/features/college-admin/types/examination-dashboard";
import { cn } from "@/lib/utils";

function withSessionId(href: string, sessionId?: string | null): string {
  if (!sessionId || !href || href.includes("session_id=")) return href;
  const join = href.includes("?") ? "&" : "?";
  return `${href}${join}session_id=${encodeURIComponent(sessionId)}`;
}

export function ExaminationWorkflowStepper({
  steps,
  sessionId,
  linkMode = "page",
  onStepNavigate,
}: {
  steps: ExaminationWorkflowStep[];
  sessionId?: string | null;
  linkMode?: "page" | "modal";
  onStepNavigate?: (href: string) => void;
}) {
  return (
    <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white px-4 py-4 shadow-[0_1px_2px_rgba(15,23,42,0.04)] sm:px-6">
      <div className="flex flex-wrap items-center gap-y-3 sm:flex-nowrap">
        {steps.map((wizardStep, index) => {
          const active = wizardStep.status === "active";
          const done = wizardStep.status === "done";
          const inner = (
            <>
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
                  "ml-2 hidden truncate text-left text-[12px] sm:inline sm:text-[13px]",
                  active ? "font-semibold text-[#111827]" : "font-medium text-[#9ca3af]",
                )}
              >
                {wizardStep.label}
              </span>
            </>
          );
          const href = wizardStep.href ? withSessionId(wizardStep.href, sessionId) : "";
          const useModalNav = linkMode === "modal" && Boolean(onStepNavigate) && Boolean(href) && !active;

          return (
            <div key={wizardStep.key} className="flex min-w-0 flex-1 items-center last:flex-none">
              {useModalNav ? (
                <button
                  type="button"
                  onClick={() => onStepNavigate?.(href)}
                  className="flex min-w-0 items-center hover:opacity-90"
                >
                  {inner}
                </button>
              ) : href && !active ? (
                <Link href={href} className="flex min-w-0 items-center hover:opacity-90">
                  {inner}
                </Link>
              ) : (
                <div className="flex min-w-0 items-center">{inner}</div>
              )}
              {index < steps.length - 1 ? (
                <div className="mx-2 hidden h-px min-w-[1rem] flex-1 bg-[#e5e7eb] sm:block" aria-hidden />
              ) : null}
            </div>
          );
        })}
      </div>
    </section>
  );
}