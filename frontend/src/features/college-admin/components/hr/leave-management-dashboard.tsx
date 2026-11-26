"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { Settings2Icon } from "@/components/icons/erp/generated/settings-2";
import { HrRecruitmentSubNav } from "@/features/college-admin/components/hr/hr-recruitment-sub-nav";
import {
  CollegeAdminKpiGrid,
  CollegeAdminUserDashboardKpiCard,
} from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useHrLeaveManagementPage } from "@/features/college-admin/hooks/use-hr-attendance-leave";
import type { HrLeaveManagementPage } from "@/features/college-admin/types/hr-attendance-leave";
import type { HrRecruitmentPagination, HrRecruitmentSubNavItem } from "@/features/college-admin/types/hr-recruitment";
import { cn } from "@/lib/utils";

const TABLE_HEADERS = ["Employee", "Leave type", "Dates", "Days", "Approver", "Status"];

const DEFAULT_SUB_NAV: HrRecruitmentSubNavItem[] = [
  { key: "employee-attendance", label: "Employee attendance", href: "/college-admin/hr/employee-attendance" },
  { key: "leave-management", label: "Leave management", href: "/college-admin/hr/leave-management" },
];

const PLACEHOLDER_KPIS = [
  { key: "applications", label: "Applications", value: "0", hint_line: "Pending", hint_tone: "neutral" },
  { key: "approved_month", label: "Approved this month", value: "0", hint_line: "—", hint_tone: "neutral" },
  { key: "on_leave_week", label: "On leave this week", value: "0", hint_line: "—", hint_tone: "neutral" },
  { key: "low_balance", label: "Balance below 3 days", value: "0", hint_line: "Employees", hint_tone: "neutral" },
];

function StatusPill({ label, tone }: { label: string; tone: string }) {
  const styles: Record<string, string> = {
    success: "bg-[#ecfdf5] text-[#047857]",
    warning: "bg-[#fff7ed] text-[#c2410c]",
    error: "bg-[#fef2f2] text-[#b91c1c]",
    info: "bg-[#eff6ff] text-[#1d4ed8]",
    muted: "bg-[#f3f4f6] text-[#6b7280]",
  };
  const dot: Record<string, string> = {
    success: "bg-[#10b981]",
    warning: "bg-[#f97316]",
    error: "bg-[#ef4444]",
    info: "bg-[#3b82f6]",
    muted: "bg-[#9ca3af]",
  };
  const key = tone in styles ? tone : "muted";
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-medium",
        styles[key],
      )}
    >
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
      <button
        type="button"
        className="rounded border border-[#dce3ec] px-2 py-1 disabled:opacity-40"
        disabled={!pagination.has_previous}
        onClick={() => onPage(Math.max(1, pagination.page - 1))}
      >
        ‹
      </button>
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
              num === pagination.page
                ? "border-[#245dd8] bg-[#eff6ff] text-[#245dd8]"
                : "border-[#dce3ec]",
            )}
            onClick={() => onPage(num)}
          >
            {num}
          </button>
        ),
      )}
      <button
        type="button"
        className="rounded border border-[#dce3ec] px-2 py-1 disabled:opacity-40"
        disabled={!pagination.has_next}
        onClick={() => onPage(pagination.page + 1)}
      >
        ›
      </button>
    </div>
  );
}

function mergeView(data: HrLeaveManagementPage | undefined) {
  const emptyPagination: HrRecruitmentPagination = {
    page: 1,
    page_size: 4,
    total: 0,
    total_pages: 0,
    page_numbers: [],
    has_previous: false,
    has_next: false,
  };
  return {
    page_title: data?.page_title ?? "Leave Management",
    page_subtitle: data?.page_subtitle ?? "Leave balances, applications and calendar",
    leave_policy_label: data?.leave_policy_label ?? "Leave policy",
    leave_policy_href: data?.leave_policy_href ?? "/college-admin/hr/hr-settings-policies",
    sub_nav: data?.sub_nav?.length ? data.sub_nav : DEFAULT_SUB_NAV,
    kpis: data?.kpis?.length ? data.kpis : PLACEHOLDER_KPIS,
    applications_section_title: data?.applications_section_title ?? "Leave applications",
    table_headers: data?.table_headers?.length ? data.table_headers : TABLE_HEADERS,
    application_rows: data?.application_rows ?? [],
    showing_label: data?.showing_label ?? "Showing 0 of 0",
    pagination: data?.pagination ?? emptyPagination,
    footer_disclaimer: data?.footer_disclaimer ?? "Live institutional data · Leave applications · All times IST",
    footer_snapshot_label: data?.footer_snapshot_label ?? "",
  };
}

export function LeaveManagementDashboard() {
  const [page, setPage] = useState(1);
  const queryParams = useMemo(() => ({ page, page_size: 4 }), [page]);
  const { data, isLoading, isError, error, refetch, isFetching } = useHrLeaveManagementPage(queryParams);
  const view = mergeView(data);

  return (
    <div className="space-y-5" data-figma-frame="160:8880">
      <HrRecruitmentSubNav items={view.sub_nav} />

      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">{view.page_title}</h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">{view.page_subtitle}</p>
        </div>
        <Link
          href={view.leave_policy_href}
          className="inline-flex h-9 shrink-0 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
        >
          <Settings2Icon className="size-3.5" aria-hidden />
          {view.leave_policy_label}
        </Link>
      </div>

      {isLoading || isFetching ? (
        <p className="text-[12px] text-[#9ca3af]">{isLoading ? "Loading leave data…" : "Updating…"}</p>
      ) : null}

      {isError ? <QueryState isError={isError} error={error} onRetry={() => void refetch()} /> : null}

      {!isError ? (
        <>
          <CollegeAdminKpiGrid>
            {view.kpis.map((kpi, index) => (
              <CollegeAdminUserDashboardKpiCard key={kpi.key} kpi={kpi} index={index} />
            ))}
          </CollegeAdminKpiGrid>

          <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
            <div className="border-b border-[#f1f5f9] px-5 py-3.5">
              <h3 className="text-[14px] font-semibold text-[#111827]">{view.applications_section_title}</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[44rem] text-left text-[13px]">
                <thead>
                  <tr className="border-b border-[#f1f5f9] text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                    {view.table_headers.map((header, index) => (
                      <th
                        key={header}
                        className={cn(
                          "pb-3 pt-4 font-medium",
                          index === 0 ? "pl-5 pr-3" : "pr-3",
                          index === view.table_headers.length - 1 ? "pr-5" : "",
                        )}
                      >
                        {header}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#f1f5f9]">
                  {view.application_rows.length ? (
                    view.application_rows.map((row) => (
                      <tr key={row.leave_request_id} className="hover:bg-[#f9fafb]">
                        <td className="pl-5 py-3 pr-3 font-medium text-[#111827]">
                          <Link href={row.detail_href} className="hover:text-[#245dd8]">
                            {row.employee_name}
                          </Link>
                        </td>
                        <td className="py-3 pr-3 text-[#374151]">{row.leave_type_label}</td>
                        <td className="py-3 pr-3 text-[#374151]">{row.dates_label}</td>
                        <td className="py-3 pr-3 tabular-nums text-[#374151]">{row.days_label}</td>
                        <td className="py-3 pr-3 text-[#6b7280]">{row.approver_label}</td>
                        <td className="py-3 pr-5">
                          <StatusPill label={row.status_label} tone={row.status_tone} />
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={view.table_headers.length} className="px-5 py-10 text-center text-sm text-[#9ca3af]">
                        No leave applications yet. Applications will appear when employees submit leave requests.
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