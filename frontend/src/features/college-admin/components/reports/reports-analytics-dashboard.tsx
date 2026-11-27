"use client";

import { CollegeAdminModulePageLayout } from "@/features/college-admin/components/layout/college-admin-module-page-layout";
import { CollegeAdminModulePageHeading } from "@/features/college-admin/components/layout/college-admin-module-page-heading";
import Link from "next/link";
import { useMemo, useState } from "react";

import { CollegeAdminPlusActionLabel } from "@/features/college-admin/components/ui/college-admin-plus-action";
import {
  CollegeAdminKpiGrid,
  CollegeAdminUserDashboardKpiCard,
} from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { CollegeAdminSectionNavIcon } from "@/features/college-admin/components/ui/college-admin-section-nav-icons";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useReportsDashboardPage } from "@/features/college-admin/hooks/use-reports-dashboard";
import type { ReportsDashboardPage, ReportsDashboardPagination } from "@/features/college-admin/types/reports-dashboard";
import { cn } from "@/lib/utils";

function TablePagination({
  pagination,
  onPage,
}: {
  pagination: ReportsDashboardPagination;
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

const emptyPagination: ReportsDashboardPagination = {
  page: 1,
  page_size: 4,
  total: 0,
  total_pages: 0,
  page_numbers: [],
  has_previous: false,
  has_next: false,
};

function mergeView(data: ReportsDashboardPage | undefined) {
  return {
    page_title: data?.page_title ?? "",
    page_subtitle: data?.page_subtitle ?? "",
    create_report_label: data?.create_report_label ?? "",
    create_report_href: data?.create_report_href ?? "#",
    reports_section_title: data?.reports_section_title ?? "",
    groups_section_title: data?.groups_section_title ?? "",
    table_headers: data?.table_headers ?? [],
    report_rows: data?.report_rows ?? [],
    group_rows: data?.group_rows ?? [],
    empty_table_message: data?.empty_table_message ?? "",
    empty_groups_message: data?.empty_groups_message ?? "",
    showing_label: data?.showing_label ?? "",
    kpis: data?.kpis ?? [],
    pagination: data?.pagination ?? emptyPagination,
  };
}

export function ReportsAnalyticsDashboard() {
  const [page, setPage] = useState(1);
  const queryParams = useMemo(() => ({ page, page_size: 4 }), [page]);
  const { data, isLoading, isError, error, refetch, isFetching } = useReportsDashboardPage(queryParams);
  const view = mergeView(data);

  return (
    <CollegeAdminModulePageLayout figmaFrame="161:14939">
      <CollegeAdminModulePageHeading
        title={view.page_title || "Reports Dashboard"}
        subtitle={view.page_subtitle || undefined}
        actions={
          <Link
            href={view.create_report_href}
            className="inline-flex h-9 shrink-0 items-center rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
          >
            <CollegeAdminPlusActionLabel label={view.create_report_label || "Create report"} />
          </Link>
        }
      />

      {isLoading || isFetching ? (
        <p className="text-[12px] text-[#9ca3af]">{isLoading ? "Loading reports…" : "Updating…"}</p>
      ) : null}

      {isError ? (
        <QueryState isError={isError} error={error} onRetry={() => void refetch()}>
          <></>
        </QueryState>
      ) : !isError ? (
        <>
          <CollegeAdminKpiGrid>
            {view.kpis.map((kpi, index) => (
              <CollegeAdminUserDashboardKpiCard key={kpi.key} kpi={kpi} index={index} />
            ))}
          </CollegeAdminKpiGrid>

          <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_300px]">
            <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                <h3 className="text-[14px] font-semibold text-[#111827]">
                  {view.reports_section_title || "Reports"}
                </h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[48rem] text-left text-[13px]">
                  <thead>
                    <tr className="border-b border-[#f1f5f9] text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                      {view.table_headers.map((header, index, headers) => (
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
                    {view.report_rows.length ? (
                      view.report_rows.map((row) => (
                        <tr key={row.row_id} className="text-[#374151] hover:bg-[#f9fafb]">
                          <td className="pl-5 py-3 pr-3 font-medium text-[#111827]">
                            <Link href={row.detail_href} className="hover:text-[#245dd8]">
                              {row.report_label}
                            </Link>
                          </td>
                          <td className="py-3 pr-3 text-right text-[#6b7280]">{row.period_label}</td>
                          <td className="py-3 pr-3 text-right text-[#6b7280]">{row.format_label}</td>
                          <td className="py-3 pr-3 text-right text-[#6b7280] tabular-nums">{row.last_run_label}</td>
                          <td className="py-3 pr-5 text-right text-[#6b7280]">{row.schedule_label}</td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td
                          colSpan={Math.max(view.table_headers.length, 1)}
                          className="px-5 py-10 text-center text-sm text-[#9ca3af]"
                        >
                          {view.empty_table_message}
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

            <section className="h-fit overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                <h3 className="text-[14px] font-semibold text-[#111827]">
                  {view.groups_section_title || "Report groups"}
                </h3>
              </div>
              <ul className="divide-y divide-[#f1f5f9]">
                {view.group_rows.length ? (
                  view.group_rows.map((group) => (
                    <li key={group.group_key}>
                      <Link
                        href={group.detail_href}
                        className="flex items-center gap-3 px-5 py-3.5 hover:bg-[#f9fafb]"
                      >
                        <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-[#eff6ff] text-[#245dd8]">
                          <CollegeAdminSectionNavIcon navKey={group.icon_key} className="size-4" />
                        </span>
                        <div className="min-w-0 flex-1">
                          <p className="text-[13px] font-medium text-[#111827]">{group.label}</p>
                          <p className="text-[12px] text-[#6b7280]">{group.count_label}</p>
                        </div>
                        <span className="rounded-full bg-[#245dd8] px-2 py-0.5 text-[11px] font-medium tabular-nums text-white">
                          {group.count_badge}
                        </span>
                      </Link>
                    </li>
                  ))
                ) : (
                  <li className="px-5 py-10 text-center text-sm text-[#9ca3af]">{view.empty_groups_message}</li>
                )}
              </ul>
            </section>
          </div>
        </>
      ) : null}
    </CollegeAdminModulePageLayout>
  );
}