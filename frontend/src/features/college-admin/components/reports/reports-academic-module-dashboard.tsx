"use client";

import { CollegeAdminModulePageLayout } from "@/features/college-admin/components/layout/college-admin-module-page-layout";
import { useCallback, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

import { ChevronRightIcon } from "@/components/icons/erp/generated/chevron-right";
import { Button } from "@/components/ui/button";
import { CollegeAdminDownload } from "@/features/college-admin/components/layout/college-admin-erp-icons";
import {
  CollegeAdminKpiGrid,
  CollegeAdminUserDashboardKpiCard,
} from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { onCollegeAdminMutationError } from "@/features/college-admin/context/college-admin-validation-context";
import {
  useReportsModulePage,
  useRunReportsModuleReport,
} from "@/features/college-admin/hooks/use-reports-academic-module";
import type {
  ReportsAcademicHighlightBar,
  ReportsAcademicPageQuery,
  ReportsAcademicPagination,
  ReportsModuleSection,
} from "@/features/college-admin/types/reports-academic-module";
import { cn } from "@/lib/utils";

function HighlightBar({ bar }: { bar: ReportsAcademicHighlightBar }) {
  const fill: Record<string, string> = {
    success: "bg-[#10b981]",
    info: "bg-[#3b82f6]",
    warning: "bg-[#d97706]",
    muted: "bg-[#9ca3af]",
  };
  const color = fill[bar.tone] ?? fill.info;
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between gap-2 text-[12px]">
        <span className="font-medium text-[#111827]">{bar.department_label}</span>
        <span className="tabular-nums text-[#6b7280]">{bar.percent_value}%</span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-[#e5e7eb]">
        <div className={cn("h-full rounded-full transition-all", color)} style={{ width: `${bar.percent_value}%` }} />
      </div>
    </div>
  );
}

function TablePagination({
  pagination,
  onPage,
}: {
  pagination: ReportsAcademicPagination;
  onPage: (page: number) => void;
}) {
  if (pagination.total_pages <= 0) return null;
  return (
    <nav className="flex flex-wrap items-center justify-end gap-1" aria-label="Reports pagination">
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

type Props = { pageKey: string; section?: ReportsModuleSection; figmaFrame?: string };

export function ReportsAcademicModuleDashboard({ pageKey, section = "academic", figmaFrame }: Props) {
  const [page, setPage] = useState(1);
  const [departmentId, setDepartmentId] = useState("");
  const [academicYear, setAcademicYear] = useState("");

  const queryParams = useMemo<ReportsAcademicPageQuery>(
    () => ({
      page,
      page_size: 4,
      department_id: departmentId || undefined,
      academic_year: academicYear || undefined,
    }),
    [page, departmentId, academicYear],
  );

  const { data, isLoading, isError, error, refetch, isFetching } = useReportsModulePage(section, pageKey, queryParams);
  const runReport = useRunReportsModuleReport(section, pageKey, queryParams);

  useEffect(() => {
    setPage(1);
  }, [departmentId, academicYear]);

  useEffect(() => {
    if (data?.academic_year_label && !academicYear) {
      const raw = data.academic_year_options[0]?.value ?? data.academic_year_label.replace(/^AY\s+/, "");
      setAcademicYear(raw);
    }
  }, [data, academicYear]);

  const handleExport = useCallback(() => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `reports-${pageKey}-${new Date(data.generated_at).toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data, pageKey]);

  const handleRun = () => {
    runReport.mutate(undefined, {
      onSuccess: () => toast.success("Report run queued"),
      onError: onCollegeAdminMutationError,
    });
  };

  return (
    <CollegeAdminModulePageLayout figmaFrame={figmaFrame}>
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Reports"}
          </h2>
          {data?.page_subtitle ? (
            <p className="mt-1 text-[14px] text-[#6b7280]">{data.page_subtitle}</p>
          ) : null}
        </div>
        <div className="flex shrink-0 flex-wrap items-center gap-2">
          <Button
            type="button"
            variant="outline"
            className="h-9 gap-1.5 border-[#dce3ec] text-xs"
            disabled={!data}
            onClick={handleExport}
          >
            <CollegeAdminDownload className="size-3.5" aria-hidden />
            {data?.export_label ?? "Export"}
          </Button>
          <Button
            type="button"
            className="h-9 gap-1.5 bg-[#245dd8] text-xs font-medium text-white hover:bg-[#1f4fb8]"
            disabled={runReport.isPending}
            onClick={handleRun}
          >
            {data?.run_report_label ?? "Run report"}
            <ChevronRightIcon className="size-3.5" aria-hidden />
          </Button>
        </div>
      </div>

      {data ? (
        <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between">
          <div className="flex flex-wrap items-center gap-2">
            <select
              aria-label="Academic year"
              className="h-9 rounded-md border border-[#dce3ec] bg-white px-3 text-[13px]"
              value={academicYear}
              onChange={(e) => setAcademicYear(e.target.value)}
            >
              {data.academic_year_options.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label || data.academic_year_label}
                </option>
              ))}
            </select>
            <select
              aria-label="Department"
              className="h-9 min-w-[10rem] rounded-md border border-[#dce3ec] bg-white px-3 text-[13px]"
              value={departmentId}
              onChange={(e) => setDepartmentId(e.target.value)}
            >
              {data.department_options.map((opt) => (
                <option key={opt.value || "all"} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-[#eff6ff] px-2.5 py-1 text-[11px] font-medium text-[#1d4ed8]">
              <span className="size-1.5 rounded-full bg-[#3b82f6]" aria-hidden />
              {data.scope_badge_label}
            </span>
          </div>
          <span className="text-[12px] text-[#9ca3af]">{data.updated_at_label}</span>
        </div>
      ) : null}

      {isLoading || isFetching ? (
        <p className="text-[12px] text-[#9ca3af]">{isLoading ? "Loading…" : "Updating…"}</p>
      ) : null}

      {isError ? (
        <QueryState isError={isError} error={error} onRetry={() => void refetch()}>
          <></>
        </QueryState>
      ) : !isError && data ? (
        <>
          <CollegeAdminKpiGrid>
            {data.kpis.map((kpi, index) => (
              <CollegeAdminUserDashboardKpiCard key={kpi.key} kpi={kpi} index={index} />
            ))}
          </CollegeAdminKpiGrid>

          <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_300px]">
            <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.reports_section_title}</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[48rem] text-left text-[13px]">
                  <thead>
                    <tr className="border-b border-[#f1f5f9] text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                      {data.table_headers.map((header, index, headers) => (
                        <th
                          key={header}
                          className={cn(
                            "pb-3 pt-4 font-medium",
                            index === 0 ? "pl-5 pr-3" : "pr-3",
                            index === headers.length - 1 ? "pr-5" : "",
                            index >= 1 ? "text-right tabular-nums" : "",
                          )}
                        >
                          {header}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#f1f5f9]">
                    {data.report_rows.length ? (
                      data.report_rows.map((row) => (
                        <tr key={row.row_key} className="hover:bg-[#f9fafb]">
                          <td className="pl-5 py-3 pr-3 font-medium text-[#111827]">{row.report_label}</td>
                          <td className="py-3 pr-3 text-right text-[#6b7280]">{row.period_label}</td>
                          <td className="py-3 pr-3 text-right text-[#6b7280]">{row.format_label}</td>
                          <td className="py-3 pr-3 text-right text-[#6b7280] tabular-nums">{row.last_run_label}</td>
                          <td className="py-3 pr-5 text-right text-[#6b7280]">{row.schedule_label}</td>
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
                <span>{data.showing_label}</span>
                <TablePagination pagination={data.pagination} onPage={setPage} />
              </div>
            </section>

            <section className="h-fit overflow-hidden rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <h3 className="mb-4 text-[14px] font-semibold text-[#111827]">{data.highlights_section_title}</h3>
              {data.highlight_bars.length ? (
                <div className="space-y-4">
                  {data.highlight_bars.map((bar) => (
                    <HighlightBar key={bar.bar_key} bar={bar} />
                  ))}
                </div>
              ) : (
                <p className="py-8 text-center text-sm text-[#9ca3af]">{data.empty_highlights_message}</p>
              )}
            </section>
          </div>
        </>
      ) : null}
    </CollegeAdminModulePageLayout>
  );
}