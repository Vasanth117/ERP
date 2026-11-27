"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { ReactNode } from "react";

import { ChevronRightIcon } from "@/components/icons/erp/generated/chevron-right";
import {
  CollegeAdminDownload,
  getCollegeAdminErpIcon,
  resolveCollegeAdminIconSlug,
} from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { ExaminationWorkflowStepper } from "@/features/college-admin/components/examinations/examination-workflow-stepper";
import { Button } from "@/components/ui/button";
import type { ExaminationWorkflowStep } from "@/features/college-admin/types/examination-dashboard";

type ExaminationCreationWorkflowHeaderProps = {
  pageTitle: string;
  pageSubtitle: string;
  backHref: string;
  saveDraftLabel?: string;
  continueLabel?: string;
  workflowSteps?: ExaminationWorkflowStep[];
  sessionId?: string | null;
  saving?: boolean;
  continuing?: boolean;
  onSaveDraft?: () => void;
  onContinue?: () => void;
  continueDisabled?: boolean;
  saveDisabled?: boolean;
  children?: ReactNode;
};

export function ExaminationCreationWorkflowHeader({
  pageTitle,
  pageSubtitle,
  backHref,
  saveDraftLabel = "Save draft",
  continueLabel = "Continue",
  workflowSteps,
  sessionId,
  saving,
  continuing,
  onSaveDraft,
  onContinue,
  continueDisabled,
  saveDisabled,
  children,
}: ExaminationCreationWorkflowHeaderProps) {
  const BackIcon = getCollegeAdminErpIcon(resolveCollegeAdminIconSlug("arrow-left"));

  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="flex gap-3">
          <Link
            href={backHref}
            className="mt-1 flex size-9 shrink-0 items-center justify-center rounded-md border border-[#dce3ec] text-[#6b7280] hover:bg-[#f9fafb]"
            aria-label="Back"
          >
            {BackIcon ? <BackIcon className="size-4" /> : "←"}
          </Link>
          <div>
            <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">{pageTitle}</h2>
            <p className="mt-1 text-[14px] text-[#6b7280]">{pageSubtitle}</p>
          </div>
        </div>
        {onSaveDraft || onContinue ? (
          <div className="flex shrink-0 flex-wrap gap-2">
            {onSaveDraft ? (
              <Button
                type="button"
                variant="outline"
                className="h-9 gap-1.5 border-[#dce3ec] text-xs font-medium"
                disabled={saving || saveDisabled}
                onClick={onSaveDraft}
              >
                <CollegeAdminDownload className="size-3.5" />
                {saveDraftLabel}
              </Button>
            ) : null}
            {onContinue ? (
              <Button
                type="button"
                className="h-9 gap-1.5 bg-[#245dd8] text-xs font-medium hover:bg-[#1f4fb8]"
                disabled={continuing || continueDisabled}
                onClick={onContinue}
              >
                {continueLabel}
                <ChevronRightIcon className="size-3.5" aria-hidden />
              </Button>
            ) : null}
          </div>
        ) : null}
      </div>
      {workflowSteps?.length ? <ExaminationWorkflowStepper steps={workflowSteps} sessionId={sessionId} /> : null}
      {children}
    </div>
  );
}

export function useExaminationWorkflowContinue() {
  const router = useRouter();
  return (continueHref: string | undefined) => {
    if (continueHref) router.push(continueHref);
  };
}