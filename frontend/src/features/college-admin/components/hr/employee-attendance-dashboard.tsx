"use client";

import { useCallback, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { CollegeAdminDownload } from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { HrRecruitmentSubNav } from "@/features/college-admin/components/hr/hr-recruitment-sub-nav";
import {
  CollegeAdminKpiGrid,
  CollegeAdminUserDashboardKpiCard,
} from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useHrEmployeeAttendancePage } from "@/features/college-admin/hooks/use-hr-attendance-leave";
import type { HrEmployeeAttendancePage } from "@/features/college-admin/types/hr-attendance-leave";
import type { HrRecruitmentPagination, HrRecruitmentSubNavItem } from "@/features/college-admin/types/hr-recruitment";
import { cn } from "@/lib/utils";

const TABLE_HEADERS = ["Employee", "Department", "Present", "Leave", "Absent", "Rate"];

const DEFAULT_SUB_NAV: HrRecruitmentSubNavItem[] = [
  { key: "employee-attendance", label: "Employee attendance", href: "/college-admin/hr/employee-attendance" },
  { key: "leave-management", label: "Leave management", href: "/college-admin/hr/leave-management" },
];

const PLACEHOLDER_KPIS = [
  { key: "present_today", label: "Present today", value: "0", hint_line: "0%", hint_tone: "neutral" },
  { key: "on_leave", label: "On leave", value: "0", hint_line: "Approved today", hint_tone: "neutral" },
  { key: "absent", label: "Absent", value: "0", hint_line: "Unmarked", hint_tone: "neutral" },
  { key: "late_arrivals", label: "Late arrivals", value: "0", hint_line: "After shift start", hint_tone: "neutral" },
];

function TablePagination({
  pagination,
  onPage,
}: {
  pagination: HrRecruitmentPagination;
  onPage: (page: number) => void;
}) {
  if (pagination.total_pages <= 0) return null;
  return (
    <nav className="flex flex-wrap items-center justify-end gap-1" aria-label="Employee attendance pagination">
      <button
        type="button"
        className="rounded border border-[#dce3ec] px-2 py-1 text-[12px] disabled:opacity-40"
        disabled={!pagination.has_previous}
        onClick={() => onPage(Math.max(1, pagination.page - 1))}
      >
        ‹
      </button>
      {pagination.page_numbers.map((num, idx) =>
        num === -1 ? (
          <span key={`ellipsis-${idx}`} className="px-1 text-[12px] text-[#9ca3af]">
            …
          </span>
        ) : (
          <button
            key={num}
            type="button"
            onClick={() => onPage(num)}
            className={cn(
              "min-w-[1.75rem] rounded px-1.5 py-0.5 text-[12px] tabular-nums",
              num === pagination.page
                ? "bg-[#245dd8] font-medium text-white"
                : "text-[#6b7280] hover:bg-[#f3f4f6]",
            )}
          >
            {num}
          </button>
        ),
      )}
      <button
        type="button"
        className="rounded border border-[#dce3ec] px-2 py-1 text-[12px] disabled:opacity-40"
        disabled={!pagination.has_next}
        onClick={() => onPage(pagination.page + 1)}
      >
        ›
      </button>
    </nav>
  );
}

function mergeView(data: HrEmployeeAttendancePage | undefined) {
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
    page_title: data?.page_title ?? "Employee Attendance",
    page_subtitle: data?.page_subtitle ?? "Staff attendance and late arrivals",
    export_label: data?.export_label ?? "Export",
    sub_nav: data?.sub_nav?.length ? data.sub_nav : DEFAULT_SUB_NAV,
    kpis: data?.kpis?.length ? data.kpis : PLACEHOLDER_KPIS,
    attendance_table_title: data?.attendance_table_title ?? "Attendance",
    table_headers: data?.attendance_table_headers?.length ? data.attendance_table_headers : TABLE_HEADERS,
    attendance_rows: data?.attendance_rows ?? [],
    table_footer_label: data?.table_footer_label ?? "Showing 0 of 0",
    pagination: data?.table_pagination ?? emptyPagination,
    footer_disclaimer: data?.footer_disclaimer ?? "Live institutional data · Employee attendance · All times IST",
    footer_snapshot_label: data?.footer_snapshot_label ?? "",
    generated_at: data?.generated_at,
  };
}

export function EmployeeAttendanceDashboard() {
  const [page, setPage] = useState(1);
  const queryParams = useMemo(() => ({ page, page_size: 3 }), [page]);
  const { data, isLoading, isError, error, refetch, isFetching } = useHrEmployeeAttendancePage(queryParams);
  const view = mergeView(data);

  const handleExport = useCallback(() => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `employee-attendance-${new Date(data.generated_at).toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data]);

  return (
    <div className="space-y-5" data-figma-frame="160:8600">
      <HrRecruitmentSubNav items={view.sub_nav} />

      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">{view.page_title}</h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">{view.page_subtitle}</p>
        </div>
        <Button
          type="button"
          variant="outline"
          className="h-9 shrink-0 gap-1.5 border-[#dce3ec] text-xs font-medium"
          onClick={handleExport}
          disabled={isLoading || !data}
        >
          <CollegeAdminDownload className="size-3.5" />
          {view.export_label}
        </Button>
      </div>

      {isLoading || isFetching ? (
        <p className="text-[12px] text-[#9ca3af]">{isLoading ? "Loading attendance…" : "Updating…"}</p>
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
              <h3 className="text-[14px] font-semibold text-[#111827]">{view.attendance_table_title}</h3>
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
                          index >= 2 && "text-right",
                          index === view.table_headers.length - 1 ? "pr-5" : "",
                        )}
                      >
                        {header}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#f1f5f9]">
                  {view.attendance_rows.length ? (
                    view.attendance_rows.map((row) => (
                      <tr key={row.employee_user_id} className="hover:bg-[#f9fafb]">
                        <td className="pl-5 py-3 pr-3 font-medium text-[#111827]">{row.employee_name}</td>
                        <td className="py-3 pr-3 text-[#374151]">{row.department_label}</td>
                        <td className="py-3 pr-3 text-right tabular-nums text-[#374151]">{row.present_count}</td>
                        <td className="py-3 pr-3 text-right tabular-nums text-[#374151]">{row.leave_count}</td>
                        <td className="py-3 pr-3 text-right tabular-nums text-[#374151]">{row.absent_count}</td>
                        <td className="py-3 pr-5 text-right tabular-nums text-[#374151]">
                          {row.attendance_rate_pct != null ? `${row.attendance_rate_pct}%` : "—"}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={view.table_headers.length} className="px-5 py-10 text-center text-sm text-[#9ca3af]">
                        No attendance records yet. Data will appear when staff attendance is marked.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
            <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] px-5 py-3">
              <span className="text-[12px] text-[#6b7280]">{view.table_footer_label}</span>
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