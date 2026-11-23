"use client";

import { useCallback, useState } from "react";

import { Button } from "@/components/ui/button";
import { CollegeAdminDownload } from "@/features/college-admin/components/layout/college-admin-erp-icons";
import {
  CollegeAdminKpiGrid,
  CollegeAdminUserDashboardKpiCard,
} from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useFacultyAttendanceOverviewPage } from "@/features/college-admin/hooks/use-faculty-attendance-overview";
import type { FacultyAttendancePagination } from "@/features/college-admin/types/faculty-attendance-overview";
import { cn } from "@/lib/utils";

function TablePagination({
  pagination,
  onPage,
}: {
  pagination: FacultyAttendancePagination;
  onPage: (page: number) => void;
}) {
  if (pagination.total_pages <= 1) return null;
  return (
    <nav className="flex flex-wrap items-center justify-end gap-1" aria-label="Faculty attendance pagination">
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
    </nav>
  );
}

export function FacultyAttendanceOverviewDashboard() {
  const [page, setPage] = useState(1);
  const queryParams = { page };
  const { data, isLoading, isError, error, refetch } = useFacultyAttendanceOverviewPage(queryParams);

  const handleExport = useCallback(() => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `faculty-attendance-overview-${new Date(data.generated_at).toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data]);

  return (
    <div className="space-y-5" data-figma-frame="159:7592">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Faculty Attendance Overview"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">
            {data?.page_subtitle ?? "Faculty and staff attendance"}
          </p>
        </div>
        <Button
          type="button"
          variant="outline"
          className="h-9 shrink-0 gap-1.5 border-[#dce3ec] text-xs font-medium"
          onClick={handleExport}
          disabled={isLoading || !data}
        >
          <CollegeAdminDownload className="size-3.5" />
          {data?.export_label ?? "Export"}
        </Button>
      </div>


      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            <CollegeAdminKpiGrid>
              {data.kpis.map((kpi, index) => (
                <CollegeAdminUserDashboardKpiCard key={kpi.key} kpi={kpi} index={index} />
              ))}
            </CollegeAdminKpiGrid>

            <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.faculty_table_title}</h3>
              </div>
              {data.faculty_rows.length ? (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[40rem] text-left text-[13px]">
                    <thead>
                      <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                        {data.faculty_table_headers.map((header, index) => (
                          <th
                            key={header}
                            className={cn(
                              "pb-3 font-medium",
                              index === 0 ? "px-5" : "pr-3",
                              index >= 2 && "text-right",
                            )}
                          >
                            {header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#f1f5f9]">
                      {data.faculty_rows.map((row) => (
                        <tr key={row.faculty_user_id} className="hover:bg-[#f9fafb]">
                          <td className="px-5 py-3 font-medium text-[#111827]">{row.faculty_name}</td>
                          <td className="py-3 pr-3 text-[#374151]">{row.department_label}</td>
                          <td className="py-3 pr-3 text-right tabular-nums">{row.present_count}</td>
                          <td className="py-3 pr-3 text-right tabular-nums">{row.leave_count}</td>
                          <td className="py-3 pr-3 text-right tabular-nums">{row.absent_count}</td>
                          <td className="py-3 pr-5 text-right tabular-nums">
                            {row.attendance_rate_pct != null ? `${row.attendance_rate_pct}%` : "—"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="px-5 py-10 text-center text-sm text-[#9ca3af]">No faculty attendance records yet.</p>
              )}
              <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] px-5 py-3">
                <span className="text-[12px] text-[#6b7280]">{data.table_footer_label}</span>
                <TablePagination pagination={data.table_pagination} onPage={setPage} />
              </div>
            </section>

          </>
        ) : null}
      </QueryState>
    </div>
  );
}