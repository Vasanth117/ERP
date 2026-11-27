"use client";

import { CollegeAdminModulePageLayout } from "@/features/college-admin/components/layout/college-admin-module-page-layout";
import { CollegeAdminModulePageHeading } from "@/features/college-admin/components/layout/college-admin-module-page-heading";
import Link from "next/link";
import { useCallback, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { CollegeAdminDownload } from "@/features/college-admin/components/layout/college-admin-erp-icons";
import {
  CollegeAdminKpiGrid,
  CollegeAdminUserDashboardKpiCard,
} from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useLmsDashboardPage } from "@/features/college-admin/hooks/use-lms-dashboard";
import type { LmsDashboardCompletionBar, LmsDashboardPagination } from "@/features/college-admin/types/lms-dashboard";
import { cn } from "@/lib/utils";

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
  pagination: LmsDashboardPagination;
  onPage: (page: number) => void;
}) {
  if (pagination.total_pages <= 0) return null;
  return (
    <nav className="flex flex-wrap items-center justify-end gap-1" aria-label="Courses pagination">
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

function CompletionBar({ bar }: { bar: LmsDashboardCompletionBar }) {
  const pct = Math.min(100, Math.max(0, bar.completion_percent));
  const barColor =
    bar.tone === "success"
      ? "bg-[#10b981]"
      : bar.tone === "warning"
        ? "bg-[#d97706]"
        : bar.tone === "info"
          ? "bg-[#245dd8]"
          : "bg-[#9ca3af]";
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-2 text-[13px]">
        <span className="font-medium text-[#111827]">{bar.department_label}</span>
        <span className="tabular-nums font-medium text-[#374151]">{pct}%</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-[#f3f4f6]">
        <div className={cn("h-full rounded-full transition-all", barColor)} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export function LmsDashboard() {
  const [page, setPage] = useState(1);
  const queryParams = useMemo(() => ({ page, page_size: 4 }), [page]);
  const { data, isLoading, isError, error, refetch, isFetching } = useLmsDashboardPage(queryParams);

  const handleExport = useCallback(() => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `lms-dashboard-${new Date(data.generated_at).toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data]);

  return (
    <CollegeAdminModulePageLayout figmaFrame="161:11018">
      <CollegeAdminModulePageHeading
        title={data?.page_title ?? "LMS Dashboard"}
        subtitle={data?.page_subtitle}
        actions={
          <Button
            type="button"
            className="h-9 gap-1.5 bg-[#245dd8] text-xs font-medium text-white hover:bg-[#1f4fb8]"
            disabled={isLoading || !data}
            onClick={handleExport}
          >
            <CollegeAdminDownload className="size-3.5" aria-hidden />
            {data?.export_label ?? "Export"}
          </Button>
        }
      />

      {isLoading || isFetching ? (
        <p className="text-[12px] text-[#9ca3af]">{isLoading ? "Loading…" : "Updating…"}</p>
      ) : null}

      {isError ? (
        <QueryState isError={isError} error={error} onRetry={() => void refetch()}>
          <></>
        </QueryState>
      ) : !data ? null : (
        <>
          <CollegeAdminKpiGrid>
            {data.kpis.map((kpi, index) => (
              <CollegeAdminUserDashboardKpiCard key={kpi.key} kpi={kpi} index={index} />
            ))}
          </CollegeAdminKpiGrid>

          <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_320px]">
            <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.courses_section_title}</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[52rem] text-left text-[13px]">
                  <thead>
                    <tr className="border-b border-[#f1f5f9] text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                      {data.table_headers.map((header, index, headers) => (
                        <th
                          key={header}
                          className={cn(
                            "pb-3 pt-4 font-medium",
                            index === 0 ? "pl-5 pr-3" : "pr-3",
                            index === headers.length - 1 ? "pr-5" : "",
                            index >= 4 ? "text-right tabular-nums" : "",
                          )}
                        >
                          {header}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#f1f5f9]">
                    {data.course_rows.length ? (
                      data.course_rows.map((row) => (
                        <tr key={row.row_key} className="hover:bg-[#f9fafb]">
                          <td className="max-w-[14rem] truncate pl-5 py-3 pr-3 font-medium text-[#111827]">
                            <Link href={row.detail_href} className="hover:text-[#245dd8]">
                              {row.course_label}
                            </Link>
                          </td>
                          <td className="py-3 pr-3 tabular-nums text-[#6b7280]">{row.course_code}</td>
                          <td className="py-3 pr-3 text-[#6b7280]">{row.department_label}</td>
                          <td className="py-3 pr-3 text-[#6b7280]">{row.faculty_label}</td>
                          <td className="py-3 pr-3 text-right tabular-nums">
                            {row.students_count.toLocaleString("en-IN")}
                          </td>
                          <td className="py-3 pr-5 text-right">
                            <StatusPill label={row.status_label} tone={row.status_tone} />
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td
                          colSpan={Math.max(data.table_headers.length, 1)}
                          className="px-5 py-10 text-center text-sm text-[#9ca3af]"
                        >
                          {data.empty_table_message}
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
              <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
                <span>{data.count_footer_label || data.showing_label}</span>
                <TablePagination pagination={data.pagination} onPage={setPage} />
              </div>
            </section>

            <section className="h-fit rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <h3 className="mb-4 text-[14px] font-semibold text-[#111827]">{data.completion_section_title}</h3>
              {data.completion_bars.length ? (
                <div className="space-y-4">
                  {data.completion_bars.map((bar) => (
                    <CompletionBar key={bar.department_label} bar={bar} />
                  ))}
                </div>
              ) : (
                <p className="text-center text-sm text-[#9ca3af]">{data.empty_completion_message}</p>
              )}
            </section>
          </div>
        </>
      )}
    </CollegeAdminModulePageLayout>
  );
}