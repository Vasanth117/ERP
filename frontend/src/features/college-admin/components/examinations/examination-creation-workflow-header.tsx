"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { ReactNode } from "react";

import { ChevronLeftIcon } from "@/components/icons/erp/generated/chevron-left";
import { ExaminationWorkflowStepper } from "@/features/college-admin/components/examinations/examination-workflow-stepper";
import { ExaminationWorkflowHeaderActions } from "@/features/college-admin/components/examinations/examination-workflow-header-actions";
import { useExaminationCreationFlowOptional } from "@/features/college-admin/context/examination-creation-flow-context";
import type { ExaminationWorkflowStep } from "@/features/college-admin/types/examination-dashboard";

export type ExaminationCreationWorkflowHeaderProps = {
  pageTitle: string;
  pageSubtitle: string;
  backHref: string;
  backLabel?: string;
  saveDraftLabel?: string;
  continueLabel?: string;
  workflowSteps?: ExaminationWorkflowStep[];
  sessionId?: string | null;
  busy?: boolean;
  onSaveDraft?: () => void;
  onContinue?: () => void;
  continueEnabled?: boolean;
  controlsDisabled?: boolean;
  children?: ReactNode;
  /** When set, stepper uses in-modal navigation instead of page links. */
  stepLinkMode?: "page" | "modal";
  onBack?: () => void;
  onStepNavigate?: (href: string) => void;
  headerActions?: ReactNode;
};

export function ExaminationCreationWorkflowHeader({
  pageTitle,
  pageSubtitle,
  backHref,
  backLabel = "Back",
  saveDraftLabel = "Save draft",
  continueLabel = "Continue",
  workflowSteps,
  sessionId,
  busy,
  onSaveDraft,
  onContinue,
  continueEnabled = true,
  controlsDisabled,
  children,
  stepLinkMode = "page",
  onBack,
  onStepNavigate,
  headerActions,
}: ExaminationCreationWorkflowHeaderProps) {
  const disabled = Boolean(controlsDisabled || busy);

  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="min-w-0">
          <div className="flex items-center gap-1">
            {onBack ? (
              <button
                type="button"
                onClick={onBack}
                className="inline-flex size-8 shrink-0 items-center justify-center rounded-md text-[#374151] hover:bg-[#f3f4f6]"
                aria-label={backLabel}
              >
                <ChevronLeftIcon className="size-5" />
              </button>
            ) : (
              <Link
                href={backHref}
                className="inline-flex size-8 shrink-0 items-center justify-center rounded-md text-[#374151] hover:bg-[#f3f4f6]"
                aria-label={backLabel}
              >
                <ChevronLeftIcon className="size-5" />
              </Link>
            )}
            <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">{pageTitle}</h2>
          </div>
          <p className="mt-1 pl-9 text-[14px] text-[#6b7280]">{pageSubtitle}</p>
        </div>
        <ExaminationWorkflowHeaderActions
          headerActions={headerActions}
          saveDraftLabel={saveDraftLabel}
          continueLabel={continueLabel}
          onSaveDraft={onSaveDraft}
          onContinue={onContinue}
          continueEnabled={continueEnabled}
          disabled={disabled}
        />
      </div>
      {workflowSteps?.length ? (
        <ExaminationWorkflowStepper
          steps={workflowSteps}
          sessionId={sessionId}
          linkMode={stepLinkMode}
          onStepNavigate={onStepNavigate}
        />
      ) : null}
      {children}
    </div>
  );
}

export function useExaminationWorkflowContinue() {
  const router = useRouter();
  const flow = useExaminationCreationFlowOptional();
  return (continueHref: string | undefined) => {
    if (!continueHref) return;
    if (flow?.isModalOpen) {
      flow.advanceFromHref(continueHref);
      return;
    }
    router.push(continueHref);
  };
}