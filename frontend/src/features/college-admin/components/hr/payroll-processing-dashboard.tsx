"use client";

import { CollegeAdminModulePageHeading } from "@/features/college-admin/components/layout/college-admin-module-page-heading";
import { useMemo, useState } from "react";
import { toast } from "sonner";

import { CheckIcon } from "@/components/icons/erp/generated/check";
import { SendIcon } from "@/components/icons/erp/generated/send";
import { Button } from "@/components/ui/button";
import { HrRecruitmentSubNav } from "@/features/college-admin/components/hr/hr-recruitment-sub-nav";
import {
  CollegeAdminKpiGrid,
  CollegeAdminUserDashboardKpiCard,
} from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { onCollegeAdminMutationError } from "@/features/college-admin/context/college-admin-validation-context";
import {
  useHrPayrollProcessingPage,
  useProcessHrPayroll,
  useValidateHrPayroll,
} from "@/features/college-admin/hooks/use-hr-payroll";
import type { HrPayrollProcessingPage, HrPayrollWorkflowStep } from "@/features/college-admin/types/hr-payroll";
import type { HrRecruitmentPagination, HrRecruitmentSubNavItem } from "@/features/college-admin/types/hr-recruitment";
import { cn } from "@/lib/utils";

const DEFAULT_SUB_NAV: HrRecruitmentSubNavItem[] = [
  { key: "salary-structure", label: "Salary structure", href: "/college-admin/hr/salary-structure-management" },
  { key: "payroll-processing", label: "Payroll processing", href: "/college-admin/hr/payroll-processing" },
  { key: "salary-slips", label: "Salary slips", href: "/college-admin/hr/salary-slip-management" },
];

const PLACEHOLDER_KPIS = [
  { key: "employees", label: "Employees", value: "0", hint_line: "In payroll scope", hint_tone: "neutral" },
  { key: "gross", label: "Gross", value: "₹0", hint_line: "Current run", hint_tone: "neutral" },
  { key: "deductions", label: "Deductions", value: "₹0", hint_line: "Employee deductions", hint_tone: "neutral" },
  { key: "net_payable", label: "Net payable", value: "₹0", hint_line: "After deductions", hint_tone: "neutral" },
];

const DEFAULT_STEPS: HrPayrollWorkflowStep[] = [
  { key: "attendance_lock", label: "Attendance lock", state: "current" },
  { key: "calculate", label: "Calculate", state: "upcoming" },
  { key: "validate", label: "Validate", state: "upcoming" },
  { key: "approve", label: "Approve", state: "upcoming" },
  { key: "process", label: "Process", state: "upcoming" },
  { key: "slips", label: "Slips", state: "upcoming" },
];

function WorkflowStepper({ steps }: { steps: HrPayrollWorkflowStep[] }) {
  const items = steps.length ? steps : DEFAULT_STEPS;
  return (
    <ol className="flex flex-wrap items-start gap-2 border-b border-[#e8ecf2] pb-5">
      {items.map((step, index) => (
        <li key={step.key} className="flex min-w-[5.5rem] flex-1 flex-col items-center gap-1.5 text-center">
          <span
            className={cn(
              "flex size-7 items-center justify-center rounded-full border text-[11px] font-semibold",
              step.state === "complete"
                ? "border-[#245dd8] bg-[#245dd8] text-white"
                : step.state === "current"
                  ? "border-[#245dd8] text-[#245dd8]"
                  : "border-[#e5e7eb] text-[#9ca3af]",
            )}
          >
            {step.state === "complete" ? <CheckIcon className="size-3.5" aria-hidden /> : index + 1}
          </span>
          <span
            className={cn(
              "text-[11px] font-medium leading-tight",
              step.state === "current" ? "text-[#245dd8]" : step.state === "complete" ? "text-[#111827]" : "text-[#9ca3af]",
            )}
          >
            {step.label}
          </span>
        </li>
      ))}
    </ol>
  );
}

function StatusPill({ label }: { label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-[#fff7ed] px-2.5 py-0.5 text-[11px] font-medium text-[#c2410c]">
      <span className="size-1.5 rounded-full bg-[#f97316]" />
      {label}
    </span>
  );
}

function TablePagination({
  pagination,
  onPage,
}: {
  pagination: HrRecruitmentPagination;
  onPage: (page: number) => void;
}) {
  if (pagination.total_pages <= 0) return null;
  return (
    <div className="flex items-center gap-1">
      {pagination.page_numbers.map((num, index) =>
        num === -1 ? (
          <span key={`ellipsis-${index}`} className="px-1">
            …
          </span>
        ) : (
          <button
            key={num}
            type="button"
            className={cn(
              "min-w-8 rounded border px-2 py-1 tabular-nums",
              num === pagination.page ? "border-[#245dd8] bg-[#eff6ff] text-[#245dd8]" : "border-[#dce3ec]",
            )}
            onClick={() => onPage(num)}
          >
            {num}
          </button>
        ),
      )}
    </div>
  );
}

function mergeView(data: HrPayrollProcessingPage | undefined) {
  const emptyPagination: HrRecruitmentPagination = {
    page: 1,
    page_size: 5,
    total: 0,
    total_pages: 0,
    page_numbers: [],
    has_previous: false,
    has_next: false,
  };
  return {
    page_title: data?.page_title ?? "Payroll Processing",
    page_subtitle: data?.page_subtitle ?? "Payroll run",
    validate_label: data?.validate_label ?? "Validate",
    process_payroll_label: data?.process_payroll_label ?? "Process payroll",
    can_validate: data?.can_validate ?? false,
    can_process: data?.can_process ?? true,
    action_blocked_message: data?.action_blocked_message ?? null,
    payroll_run_id: data?.payroll_run_id ?? undefined,
    sub_nav: data?.sub_nav?.length ? data.sub_nav : DEFAULT_SUB_NAV,
    workflow_steps: data?.workflow_steps?.length ? data.workflow_steps : DEFAULT_STEPS,
    kpis: data?.kpis?.length ? data.kpis : PLACEHOLDER_KPIS,
    exceptions_section_title: data?.exceptions_section_title ?? "Exceptions",
    exception_table_headers: data?.exception_table_headers ?? ["Employee", "Issue", "Impact", "Owner", "Status"],
    exception_rows: data?.exception_rows ?? [],
    exceptions_showing_label: data?.exceptions_showing_label ?? "0 of 0",
    exceptions_pagination: data?.exceptions_pagination ?? emptyPagination,
    footer_disclaimer: data?.footer_disclaimer ?? "",
    footer_snapshot_label: data?.footer_snapshot_label ?? "",
  };
}

export function PayrollProcessingDashboard() {
  const [page, setPage] = useState(1);
  const queryParams = useMemo(() => ({ page, page_size: 5 }), [page]);
  const { data, isLoading, isError, error, refetch, isFetching } = useHrPayrollProcessingPage(queryParams);
  const view = mergeView(data);

  const validate = useValidateHrPayroll(view.payroll_run_id);
  const process = useProcessHrPayroll(view.payroll_run_id);

  const onValidate = () => {
    validate.mutate(undefined, {
      onSuccess: () => toast.success("Payroll validated"),
      onError: onCollegeAdminMutationError,
    });
  };

  const onProcess = () => {
    process.mutate(undefined, {
      onSuccess: (res) => toast.success(`Payroll updated (${res.status.replace(/_/g, " ")})`),
      onError: onCollegeAdminMutationError,
    });
  };

  return (
    <div className="space-y-5" data-figma-frame="160:9787">
      <HrRecruitmentSubNav items={view.sub_nav} />

      <CollegeAdminModulePageHeading title={view.page_title} subtitle={view.page_subtitle} actions={<><Button
            type="button"
            variant="outline"
            className="h-9 gap-1.5 text-xs"
            disabled={!view.can_validate || validate.isPending}
            onClick={onValidate}
          >
            <CheckIcon className="size-3.5" aria-hidden />
            {view.validate_label}
          </Button>
          <Button
            type="button"
            className="h-9 gap-1.5 bg-[#245dd8] text-xs text-white hover:bg-[#1f4fb8]"
            disabled={!view.can_process || process.isPending}
            onClick={onProcess}
          >
            <SendIcon className="size-3.5" aria-hidden />
            {view.process_payroll_label}
          </Button></>} />

      {view.action_blocked_message ? (
        <p className="rounded-lg border border-[#fef3c7] bg-[#fffbeb] px-4 py-3 text-[13px] text-[#92400e]">
          {view.action_blocked_message}
        </p>
      ) : null}

      {isLoading || isFetching ? (
        <p className="text-[12px] text-[#9ca3af]">{isLoading ? "Loading payroll…" : "Updating…"}</p>
      ) : null}

      {isError ? <QueryState isError={isError} error={error} onRetry={() => void refetch()} /> : null}

      {!isError ? (
        <>
          <WorkflowStepper steps={view.workflow_steps} />

          <CollegeAdminKpiGrid>
            {view.kpis.map((kpi, index) => (
              <CollegeAdminUserDashboardKpiCard key={kpi.key} kpi={kpi} index={index} />
            ))}
          </CollegeAdminKpiGrid>

          <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
            <div className="border-b border-[#f1f5f9] px-5 py-3.5">
              <h3 className="text-[14px] font-semibold text-[#111827]">{view.exceptions_section_title}</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[40rem] text-left text-[13px]">
                <thead>
                  <tr className="border-b border-[#f1f5f9] text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                    {view.exception_table_headers.map((header, index) => (
                      <th
                        key={header}
                        className={cn("pb-3 pt-4 font-medium", index === 0 ? "pl-5 pr-3" : "pr-3", index === view.exception_table_headers.length - 1 ? "pr-5" : "")}
                      >
                        {header}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#f1f5f9]">
                  {view.exception_rows.length ? (
                    view.exception_rows.map((row) => (
                      <tr key={row.row_key} className="hover:bg-[#f9fafb]">
                        <td className="pl-5 py-3 pr-3 font-medium text-[#111827]">{row.employee_label}</td>
                        <td className="py-3 pr-3 text-[#374151]">{row.issue_label}</td>
                        <td className="py-3 pr-3 text-[#374151]">{row.impact_label}</td>
                        <td className="py-3 pr-3 text-[#6b7280]">{row.owner_label}</td>
                        <td className="py-3 pr-5">
                          <StatusPill label={row.status_label} />
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={view.exception_table_headers.length} className="px-5 py-10 text-center text-sm text-[#9ca3af]">
                        No exceptions for this payroll run.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
            <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
              <span>{view.exceptions_showing_label}</span>
              <TablePagination pagination={view.exceptions_pagination} onPage={setPage} />
            </div>
          </section>

          <footer className="flex flex-col gap-1 text-[11px] text-[#9ca3af] sm:flex-row sm:items-center sm:justify-between">
            <p>{view.footer_disclaimer}</p>
            {view.footer_snapshot_label ? <p>{view.footer_snapshot_label}</p> : null}
          </footer>
        </>
      ) : null}
    </div>
  );
}