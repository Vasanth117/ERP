"use client";

import { CollegeAdminModulePageHeading } from "@/features/college-admin/components/layout/college-admin-module-page-heading";
import { useMemo, useState } from "react";
import { toast } from "sonner";

import { FilePlusIcon } from "@/components/icons/erp/generated/file-plus";
import { SendIcon } from "@/components/icons/erp/generated/send";
import { Button } from "@/components/ui/button";
import { HrRecruitmentSubNav } from "@/features/college-admin/components/hr/hr-recruitment-sub-nav";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { onCollegeAdminMutationError } from "@/features/college-admin/context/college-admin-validation-context";
import {
  useGenerateHrSalarySlips,
  useHrSalarySlipManagementPage,
  usePublishHrSalarySlips,
} from "@/features/college-admin/hooks/use-hr-payroll";
import type { HrSalarySlipManagementPage } from "@/features/college-admin/types/hr-payroll";
import type { HrRecruitmentPagination, HrRecruitmentSubNavItem } from "@/features/college-admin/types/hr-recruitment";
import { cn } from "@/lib/utils";

const DEFAULT_SUB_NAV: HrRecruitmentSubNavItem[] = [
  { key: "salary-structure", label: "Salary structure", href: "/college-admin/hr/salary-structure-management" },
  { key: "payroll-processing", label: "Payroll processing", href: "/college-admin/hr/payroll-processing" },
  { key: "salary-slips", label: "Salary slips", href: "/college-admin/hr/salary-slip-management" },
];

const TABLE_HEADERS = ["Month", "Employees", "Generated", "Published", "Failed", "Status"];

function StatusPill({ label, tone }: { label: string; tone: string }) {
  const styles: Record<string, string> = {
    success: "bg-[#ecfdf5] text-[#047857]",
    info: "bg-[#eff6ff] text-[#1d4ed8]",
    error: "bg-[#fef2f2] text-[#b91c1c]",
    muted: "bg-[#f3f4f6] text-[#6b7280]",
  };
  const dot: Record<string, string> = {
    success: "bg-[#10b981]",
    info: "bg-[#3b82f6]",
    error: "bg-[#ef4444]",
    muted: "bg-[#9ca3af]",
  };
  const key = tone in styles ? tone : "muted";
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-medium", styles[key])}>
      <span className={cn("size-1.5 rounded-full", dot[key])} />
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

function cell(value: number | null | undefined) {
  if (value === null || value === undefined) return "—";
  return value.toLocaleString("en-IN");
}

function mergeView(data: HrSalarySlipManagementPage | undefined) {
  const emptyPagination: HrRecruitmentPagination = {
    page: 1,
    page_size: 3,
    total: 0,
    total_pages: 0,
    page_numbers: [],
    has_previous: false,
    has_next: false,
  };
  return {
    page_title: data?.page_title ?? "Salary Slip Management",
    page_subtitle: data?.page_subtitle ?? "Generate and publish salary slips",
    generate_label: data?.generate_label ?? "Generate",
    publish_label: data?.publish_label ?? "Publish",
    can_generate: data?.can_generate ?? false,
    can_publish: data?.can_publish ?? false,
    generate_blocked_message: data?.generate_blocked_message ?? null,
    publish_blocked_message: data?.publish_blocked_message ?? null,
    selected_payroll_run_id: data?.selected_payroll_run_id ?? undefined,
    sub_nav: data?.sub_nav?.length ? data.sub_nav : DEFAULT_SUB_NAV,
    slips_section_title: data?.slips_section_title ?? "Salary slips",
    table_headers: data?.table_headers?.length ? data.table_headers : TABLE_HEADERS,
    slip_rows: data?.slip_rows ?? [],
    showing_label: data?.showing_label ?? "Showing 0 of 0",
    pagination: data?.pagination ?? emptyPagination,
    footer_disclaimer: data?.footer_disclaimer ?? "",
    footer_snapshot_label: data?.footer_snapshot_label ?? "",
  };
}

export function SalarySlipManagementDashboard() {
  const [page, setPage] = useState(1);
  const queryParams = useMemo(() => ({ page, page_size: 3 }), [page]);
  const { data, isLoading, isError, error, refetch, isFetching } = useHrSalarySlipManagementPage(queryParams);
  const view = mergeView(data);

  const generate = useGenerateHrSalarySlips(view.selected_payroll_run_id);
  const publish = usePublishHrSalarySlips(view.selected_payroll_run_id);

  const onGenerate = () => {
    if (!view.selected_payroll_run_id) {
      toast.error(view.generate_blocked_message ?? "No approved payroll run");
      return;
    }
    generate.mutate(undefined, {
      onSuccess: (res) => toast.success(`Generated ${res.generated} salary slip(s)`),
      onError: onCollegeAdminMutationError,
    });
  };

  const onPublish = () => {
    if (!view.selected_payroll_run_id) {
      toast.error(view.publish_blocked_message ?? "No slips to publish");
      return;
    }
    publish.mutate(undefined, {
      onSuccess: (res) => toast.success(`Published ${res.published} salary slip(s)`),
      onError: onCollegeAdminMutationError,
    });
  };

  return (
    <div className="space-y-5" data-figma-frame="160:10060">
      <HrRecruitmentSubNav items={view.sub_nav} />

      <CollegeAdminModulePageHeading title={view.page_title} subtitle={view.page_subtitle} actions={<><Button
            type="button"
            variant="outline"
            className="h-9 gap-1.5 text-xs"
            disabled={!view.can_generate || generate.isPending}
            onClick={onGenerate}
          >
            <FilePlusIcon className="size-3.5" aria-hidden />
            {view.generate_label}
          </Button>
          <Button
            type="button"
            className="h-9 gap-1.5 bg-[#245dd8] text-xs text-white hover:bg-[#1f4fb8]"
            disabled={!view.can_publish || publish.isPending}
            onClick={onPublish}
          >
            <SendIcon className="size-3.5" aria-hidden />
            {view.publish_label}
          </Button></>} />

      {isLoading || isFetching ? (
        <p className="text-[12px] text-[#9ca3af]">{isLoading ? "Loading salary slips…" : "Updating…"}</p>
      ) : null}

      {isError ? <QueryState isError={isError} error={error} onRetry={() => void refetch()} /> : null}

      {!isError ? (
        <>
          <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
            <div className="border-b border-[#f1f5f9] px-5 py-3.5">
              <h3 className="text-[14px] font-semibold text-[#111827]">{view.slips_section_title}</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[40rem] text-left text-[13px]">
                <thead>
                  <tr className="border-b border-[#f1f5f9] text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                    {view.table_headers.map((header, index) => (
                      <th
                        key={header}
                        className={cn(
                          "pb-3 pt-4 font-medium",
                          index === 0 ? "pl-5 pr-3" : "pr-3",
                          index >= 1 && index <= 4 && "text-right",
                          index === view.table_headers.length - 1 ? "pr-5" : "",
                        )}
                      >
                        {header}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#f1f5f9]">
                  {view.slip_rows.length ? (
                    view.slip_rows.map((row) => (
                      <tr key={row.period_id} className="hover:bg-[#f9fafb]">
                        <td className="pl-5 py-3 pr-3 font-medium text-[#111827]">{row.month_label}</td>
                        <td className="py-3 pr-3 text-right tabular-nums">{row.employees_count.toLocaleString("en-IN")}</td>
                        <td className="py-3 pr-3 text-right tabular-nums">{cell(row.generated_count)}</td>
                        <td className="py-3 pr-3 text-right tabular-nums">{cell(row.published_count)}</td>
                        <td className="py-3 pr-3 text-right tabular-nums">{cell(row.failed_count)}</td>
                        <td className="py-3 pr-5">
                          <StatusPill label={row.status_label} tone={row.status_tone} />
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={view.table_headers.length} className="px-5 py-10 text-center text-sm text-[#9ca3af]">
                        No payroll periods yet. Process payroll to enable salary slip generation.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
            <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
              <span>{view.showing_label}</span>
              <TablePagination pagination={view.pagination} onPage={setPage} />
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