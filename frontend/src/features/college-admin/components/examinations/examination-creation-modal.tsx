"use client";

import { useCallback, useEffect, useId, type ReactNode } from "react";
import { createPortal } from "react-dom";

import { XIcon } from "@/components/icons/erp/generated/x";
import { ExaminationConfigurationDashboard } from "@/features/college-admin/components/examinations/examination-configuration-dashboard";
import { ExaminationHallSeatingManagementDashboard } from "@/features/college-admin/components/examinations/examination-hall-seating-management-dashboard";
import { ExamTimetableManagementDashboard } from "@/features/college-admin/components/examinations/exam-timetable-management-dashboard";
import { InternalExternalAssessmentDashboard } from "@/features/college-admin/components/examinations/internal-external-assessment-dashboard";
import { MarksEntryManagementDashboard } from "@/features/college-admin/components/examinations/marks-entry-management-dashboard";
import { ResultApprovalDashboard } from "@/features/college-admin/components/examinations/result-approval-dashboard";
import {
  EXAMINATION_CREATION_STEP_SLUGS,
  useExaminationCreationFlow,
} from "@/features/college-admin/context/examination-creation-flow-context";

function StepContent({ slug }: { slug: (typeof EXAMINATION_CREATION_STEP_SLUGS)[number] }) {
  switch (slug) {
    case "examination-configuration":
      return <ExaminationConfigurationDashboard />;
    case "internal-external-assessment":
      return <InternalExternalAssessmentDashboard />;
    case "exam-timetable-management":
      return <ExamTimetableManagementDashboard />;
    case "examination-hall-seating-management":
      return <ExaminationHallSeatingManagementDashboard />;
    case "marks-entry-management":
      return <MarksEntryManagementDashboard />;
    case "result-approval":
      return <ResultApprovalDashboard />;
    default:
      return null;
  }
}

export function ExaminationCreationModal() {
  const titleId = useId();
  const { isModalOpen, closeCreation, stepSlug } = useExaminationCreationFlow();

  const onKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (event.key === "Escape") closeCreation();
    },
    [closeCreation],
  );

  useEffect(() => {
    if (!isModalOpen) return;
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [isModalOpen, onKeyDown]);

  if (!isModalOpen || typeof document === "undefined") return null;

  const shell = (
    <div className="fixed inset-0 z-[80] flex items-center justify-center bg-[#0f172a]/45 p-4 sm:p-6">
      <button
        type="button"
        className="absolute inset-0 cursor-default"
        aria-label="Close create examination"
        onClick={closeCreation}
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="relative flex max-h-[min(92vh,960px)] w-full max-w-[min(1120px,calc(100vw-2rem))] flex-col overflow-hidden rounded-xl border border-[#e8ecf2] bg-[#f8fafc] shadow-2xl"
      >
        <header className="flex items-center justify-between border-b border-[#e8ecf2] bg-white px-5 py-3.5">
          <p id={titleId} className="text-[15px] font-semibold text-[#111827]">
            Create examination
          </p>
          <button
            type="button"
            onClick={closeCreation}
            className="inline-flex size-8 items-center justify-center rounded-md text-[#6b7280] hover:bg-[#f3f4f6]"
            aria-label="Close"
          >
            <XIcon className="size-4" aria-hidden />
          </button>
        </header>
        <div className="min-h-0 flex-1 overflow-y-auto px-4 py-5 sm:px-6">
          <StepContent slug={stepSlug} />
        </div>
      </div>
    </div>
  );

  return createPortal(shell, document.body) as ReactNode;
}