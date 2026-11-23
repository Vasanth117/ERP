"use client";

import Link from "next/link";
import { useCallback, useState } from "react";
import { toast } from "sonner";

import { RefreshCwIcon } from "@/components/icons/erp/generated/refresh-cw";
import { CollegeAdminDownload } from "@/features/college-admin/components/layout/college-admin-erp-icons";
import {
  CollegeAdminKpiGrid,
  CollegeAdminUserDashboardKpiCard,
} from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useFacultyWorkloadManagementPage,
  useRebalanceFacultyWorkload,
} from "@/features/college-admin/hooks/use-faculty-workload-management";
import type { PoliciesPagination } from "@/features/college-admin/types/institution";
import { cn } from "@/lib/utils";

function StatusPill({ label, tone }: { label: string; tone: string }) {
  const styles: Record<string, string> = {
    success: "bg-[#ecfdf5] text-[#047857]",
    warning: "bg-[#fff7ed] text-[#c2410c]",
    info: "bg-[#eff6ff] text-[#1d4ed8]",
    muted: "bg-[#f3f4f6] text-[#6b7280]",
  };
  const dot: Record<string, string> = {
    success: "bg-[#10b981]",
    warning: "bg-[#f97316]",
    info: "bg-[#3b82f6]",
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
  pagination: PoliciesPagination;
  onPage: (page: number) => void;
}) {
  if (pagination.total_pages <= 1) return null;
  return (
    <nav className="flex flex-wrap items-center justify-end gap-1" aria-label="Workload pagination">
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
              "min-w-8 rounded border px-2 py-1 text-[12px] tabular-nums",
              num === pagination.page
                ? "border-[#245dd8] bg-[#eff6ff] text-[#245dd8]"
                : "border-[#dce3ec] text-[#6b7280] hover:bg-[#f3f4f6]",
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
        onClick={() => onPage(Math.min(pagination.total_pages, pagination.page + 1))}
      >
        ›
      </button>
    </nav>
  );
}


export function FacultyWorkloadManagementDashboard() {
  const [page, setPage] = useState(1);
  const { data, isLoading, isError, error, refetch } = useFacultyWorkloadManagementPage({ page });
  const rebalance = useRebalanceFacultyWorkload();

  const exportCsv = useCallback(() => {
    if (!data?.workload_rows.length) {
      toast.message("Nothing to export on this page");
      return;
    }
    const headers = data.table_headers.join(",");
    const lines = data.workload_rows.map((row) =>
      [
        row.faculty_name,
        row.department_label,
        row.theory_hours_label,
        row.lab_hours_label,
        row.total_hours_label,
        row.policy_hours_label,
        row.status_label,
      ]
        .map((v) => `"${v.replace(/"/g, '""')}"`)
        .join(","),
    );
    const blob = new Blob([[headers, ...lines].join("\n")], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "faculty-workload.csv";
    a.click();
    URL.revokeObjectURL(url);
  }, [data]);

  const onRebalance = () => {
    if (!data) return;
    rebalance.mutate(
      {
        academic_year_label: data.selected_academic_year,
        semester_label: data.selected_semester_label,
      },
      {
        onSuccess: () => {
          toast.success("Workload rebalanced from assignments");
          void refetch();
        },
        onError: (e: Error) => toast.error(e.message),
      },
    );
  };

  const isBusy = rebalance.isPending;

  return (
    <div className="space-y-5" data-figma-frame="159:5133">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Faculty Workload Management"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">{data?.page_subtitle ?? "Teaching load against policy"}</p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <button
            type="button"
            disabled={!data}
            onClick={exportCsv}
            className="inline-flex h-9 items-center gap-1.5 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb] disabled:opacity-50"
          >
            <CollegeAdminDownload className="size-3.5" aria-hidden />
            {data?.export_label ?? "Export"}
          </button>
          <button
            type="button"
            disabled={!data || isBusy}
            onClick={onRebalance}
            className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8] disabled:opacity-50"
          >
            <RefreshCwIcon className="size-3.5" aria-hidden />
            {data?.rebalance_label ?? "Rebalance"}
          </button>
        </div>
      </div>

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            <CollegeAdminKpiGrid className="grid-cols-2 lg:grid-cols-4">
              {data.kpis.map((kpi, index) => (
                <CollegeAdminUserDashboardKpiCard key={kpi.key} kpi={kpi} index={index} />
              ))}
            </CollegeAdminKpiGrid>

            <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.workload_section_title}</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[720px] text-left text-[13px]">
                  <thead className="border-b border-[#f1f5f9] bg-[#f9fafb] text-[11px] font-semibold uppercase tracking-wide text-[#6b7280]">
                    <tr>
                      {data.table_headers.map((h) => (
                        <th key={h} className="px-4 py-2.5 font-semibold">
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#f1f5f9]">
                    {data.workload_rows.map((row) => (
                      <tr key={row.record_id} className="hover:bg-[#fafbfc]">
                        <td className="px-4 py-3">
                          <Link href={row.timetable_href} className="font-medium text-[#111827] hover:text-[#245dd8]">
                            {row.faculty_name}
                          </Link>
                        </td>
                        <td className="px-4 py-3 text-[#374151]">{row.department_label}</td>
                        <td className="px-4 py-3 tabular-nums text-[#374151]">{row.theory_hours_label}</td>
                        <td className="px-4 py-3 tabular-nums text-[#374151]">{row.lab_hours_label}</td>
                        <td className="px-4 py-3 tabular-nums font-medium text-[#111827]">{row.total_hours_label}</td>
                        <td className="px-4 py-3 tabular-nums text-[#6b7280]">{row.policy_hours_label}</td>
                        <td className="px-4 py-3">
                          <StatusPill label={row.status_label} tone={row.status_tone} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="flex flex-col gap-2 border-t border-[#f1f5f9] px-5 py-3 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-[12px] text-[#6b7280]">{data.showing_label}</p>
                <TablePagination pagination={data.pagination} onPage={setPage} />
              </div>
            </section>

          </>
        ) : null}
      </QueryState>
    </div>
  );
}