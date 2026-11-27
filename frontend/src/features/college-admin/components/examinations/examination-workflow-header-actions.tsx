"use client";

import type { ReactNode } from "react";

import { ChevronRightIcon } from "@/components/icons/erp/generated/chevron-right";
import { SaveIcon } from "@/components/icons/erp/generated/save";
import {
  CollegeAdminPrimaryButton,
  CollegeAdminSecondaryButton,
} from "@/features/college-admin/components/ui/college-admin-action-button";

export function ExaminationWorkflowHeaderActions({
  headerActions,
  saveDraftLabel = "Save draft",
  continueLabel = "Continue",
  onSaveDraft,
  onContinue,
  continueEnabled = true,
  disabled,
}: {
  headerActions?: ReactNode;
  saveDraftLabel?: string;
  continueLabel?: string;
  onSaveDraft?: () => void;
  onContinue?: () => void;
  continueEnabled?: boolean;
  disabled?: boolean;
}) {
  const showContinue = Boolean(onContinue && continueEnabled);
  const hasWorkflow = Boolean(onSaveDraft || showContinue);
  const hasAny = Boolean(headerActions) || hasWorkflow;
  if (!hasAny) return null;

  return (
    <div className="flex w-full flex-wrap items-center justify-end gap-2 lg:w-auto lg:max-w-[min(100%,36rem)]">
      {headerActions ? <div className="flex flex-wrap items-center justify-end gap-2">{headerActions}</div> : null}
      {onSaveDraft ? (
        <CollegeAdminSecondaryButton disabled={disabled} onClick={onSaveDraft}>
          <SaveIcon className="size-3.5" aria-hidden />
          {saveDraftLabel}
        </CollegeAdminSecondaryButton>
      ) : null}
      {showContinue ? (
        <CollegeAdminPrimaryButton disabled={disabled} onClick={onContinue}>
          {continueLabel}
          <ChevronRightIcon className="size-3.5" aria-hidden />
        </CollegeAdminPrimaryButton>
      ) : null}
    </div>
  );
}