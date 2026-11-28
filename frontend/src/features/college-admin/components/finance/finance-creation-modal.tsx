"use client";

import { useCallback, useEffect, useId, type ReactNode } from "react";
import { createPortal } from "react-dom";

import { XIcon } from "@/components/icons/erp/generated/x";
import { FeeDemandInvoiceManagementDashboard } from "@/features/college-admin/components/finance/fee-demand-invoice-management-dashboard";
import { FeeStructureCreationStep } from "@/features/college-admin/components/finance/fee-structure-creation-step";
import { FinancialReportsDashboard } from "@/features/college-admin/components/finance/financial-reports-dashboard";
import { FinanceWorkflowStepper } from "@/features/college-admin/components/finance/finance-workflow-stepper";
import { OnlinePaymentMonitoringDashboard } from "@/features/college-admin/components/finance/online-payment-monitoring-dashboard";
import { PaymentReconciliationDashboard } from "@/features/college-admin/components/finance/payment-reconciliation-dashboard";
import { StudentFeeManagementDashboard } from "@/features/college-admin/components/finance/student-fee-management-dashboard";
import {
  CollegeAdminPrimaryButton,
  CollegeAdminSecondaryButton,
} from "@/features/college-admin/components/ui/college-admin-action-button";
import {
  FINANCE_CREATION_STEP_DEFS,
  useFinanceCreationFlow,
} from "@/features/college-admin/context/finance-creation-flow-context";
import { cn } from "@/lib/utils";

function StepContent({ stepIndex }: { stepIndex: number }) {
  switch (stepIndex) {
    case 0:
      return <FeeStructureCreationStep />;
    case 1:
      return <StudentFeeManagementDashboard />;
    case 2:
      return <FeeDemandInvoiceManagementDashboard />;
    case 3:
      return <OnlinePaymentMonitoringDashboard />;
    case 4:
      return <PaymentReconciliationDashboard />;
    case 5:
      return <FinancialReportsDashboard />;
    default:
      return null;
  }
}

export function FinanceCreationModal() {
  const titleId = useId();
  const { isModalOpen, closeCreation, stepIndex, goBack, goForward } = useFinanceCreationFlow();

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
        aria-label="Close finance setup"
        onClick={closeCreation}
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="relative flex max-h-[min(92vh,960px)] w-full max-w-[min(1120px,calc(100vw-2rem))] flex-col overflow-hidden rounded-xl border border-[#e8ecf2] bg-[#f8fafc] shadow-2xl"
      >
        <header className="flex items-center justify-between border-b border-[#e8ecf2] bg-white px-5 py-3.5">
          <div className="min-w-0">
            <p id={titleId} className="text-[15px] font-semibold text-[#111827]">
              {stepIndex === 0 ? "Create fee structure" : "Finance setup"}
            </p>
            {stepIndex === 0 ? (
              <p className="mt-0.5 text-[12px] text-[#6b7280]">
                Department, stream (UG/PG), programme, and semester-wise fee heads
              </p>
            ) : (
              <p className="mt-0.5 text-[12px] text-[#6b7280]">
                Step {stepIndex + 1} of {FINANCE_CREATION_STEP_DEFS.length} ·{" "}
                {FINANCE_CREATION_STEP_DEFS[stepIndex]?.label}
              </p>
            )}
          </div>
          <button
            type="button"
            onClick={closeCreation}
            className="inline-flex size-8 items-center justify-center rounded-md text-[#6b7280] hover:bg-[#f3f4f6]"
            aria-label="Close"
          >
            <XIcon className="size-4" aria-hidden />
          </button>
        </header>
        <div className="min-h-0 flex-1 overflow-y-auto bg-[#f8fafc] px-4 py-5 sm:px-6">
          {stepIndex > 0 ? (
            <div className="rounded-xl border border-[#e8ecf2] bg-white px-4 py-4 sm:px-5">
              <FinanceWorkflowStepper activeIndex={stepIndex} />
            </div>
          ) : null}
          <div className={stepIndex > 0 ? "mt-5" : undefined}>
            <StepContent stepIndex={stepIndex} />
          </div>
        </div>
        {stepIndex > 0 ? (
          <footer className="flex justify-between gap-2 border-t border-[#e8ecf2] bg-white px-5 py-3">
            <CollegeAdminSecondaryButton disabled={stepIndex <= 0} onClick={goBack}>
              Back
            </CollegeAdminSecondaryButton>
            {stepIndex < 5 ? (
              <CollegeAdminPrimaryButton onClick={goForward}>Continue</CollegeAdminPrimaryButton>
            ) : (
              <CollegeAdminPrimaryButton onClick={closeCreation}>Done</CollegeAdminPrimaryButton>
            )}
          </footer>
        ) : null}
      </div>
    </div>
  );

  return createPortal(shell, document.body) as ReactNode;
}