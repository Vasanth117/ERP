"use client";

import Link from "next/link";
import { useCallback, useMemo, useState } from "react";

import { CollegeAdminDownload } from "@/features/college-admin/components/layout/college-admin-erp-icons";
import {
  CollegeAdminKpiGrid,
  CollegeAdminUserDashboardKpiCard,
} from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useLibraryFineManagementPage } from "@/features/college-admin/hooks/use-library-fine-management";
import type {
  LibraryFineManagementPage,
  LibraryFineManagementPagination,
} from "@/features/college-admin/types/library-fine-management";
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
  pagination: LibraryFineManagementPagination;
  onPage: (page: number) => void;
}) {
  if (pagination.total_pages <= 0) return null;
  return (
    <nav className="flex flex-wrap items-center justify-end gap-1" aria-label="Fines pagination">
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

const emptyPagination: LibraryFineManagementPagination = {
  page: 1,
  page_size: 3,
  total: 0,
  total_pages: 0,
  page_numbers: [],
  has_previous: false,
  has_next: false,
};

function mergeView(data: LibraryFineManagementPage | undefined) {
  return {
    page_title: data?.page_title ?? "",
    page_subtitle: data?.page_subtitle ?? "",
    export_label: data?.export_label ?? "",
    kpis: data?.kpis ?? [],
    fines_section_title: data?.fines_section_title ?? "",
    table_headers: data?.table_headers ?? [],
    fine_rows: data?.fine_rows ?? [],
    empty_table_message: data?.empty_table_message ?? "",
    showing_label: data?.showing_label ?? "",
    pagination: data?.pagination ?? emptyPagination,
  };
}

export function LibraryFineManagementDashboard() {
  const [page, setPage] = useState(1);
  const queryParams = useMemo(() => ({ page, page_size: 3 }), [page]);
  const { data, isLoading, isError, error, refetch, isFetching } = useLibraryFineManagementPage(queryParams);
  const view = mergeView(data);

  const handleExport = useCallback(() => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `library-fines-${new Date(data.generated_at).toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data]);

  return (
    <div className="space-y-5" data-figma-frame="160:14067">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {view.page_title || "Fine Management"}
          </h2>
          {view.page_subtitle ? (
            <p className="mt-1 text-[14px] text-[#6b7280]">{view.page_subtitle}</p>
          ) : null}
        </div>
        <button
          type="button"
          onClick={handleExport}
          disabled={!data}
          className="inline-flex h-9 shrink-0 items-center gap-1.5 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb] disabled:opacity-50"
        >
          <CollegeAdminDownload className="size-3.5" />
          {view.export_label || "Export"}
        </button>
      </div>

      {isLoading || isFetching ? (
        <p className="text-[12px] text-[#9ca3af]">{isLoading ? "Loading fines…" : "Updating…"}</p>
      ) : null}

      {isError ? (
        <QueryState isError={isError} error={error} onRetry={() => void refetch()}>
          <></>
        </QueryState>
      ) : !data ? null : (
        <>
          <CollegeAdminKpiGrid>
            {view.kpis.map((kpi, index) => (
              <CollegeAdminUserDashboardKpiCard key={kpi.key} kpi={kpi} index={index} />
            ))}
          </CollegeAdminKpiGrid>

          <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
            <div className="border-b border-[#f1f5f9] px-5 py-3.5">
              <h3 className="text-[14px] font-semibold text-[#111827]">
                {view.fines_section_title || "Fines"}
              </h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[44rem] text-left text-[13px]">
                <thead>
                  <tr className="border-b border-[#f1f5f9] text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                    {view.table_headers.map((header, index, headers) => (
                      <th
                        key={header}
                        className={cn(
                          "pb-3 pt-4 font-medium",
                          index === 0 ? "pl-5 pr-3" : "pr-3",
                          index === headers.length - 1 ? "pr-5" : "",
                          index >= 2 ? "text-right tabular-nums" : "",
                        )}
                      >
                        {header}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#f1f5f9]">
                  {view.fine_rows.length ? (
                    view.fine_rows.map((row) => (
                      <tr key={row.fine_id} className="text-[#374151] hover:bg-[#f9fafb]">
                        <td className="pl-5 py-3 pr-3 font-medium text-[#111827]">
                          <Link href={row.detail_href} className="hover:text-[#245dd8]">
                            {row.member_name}
                          </Link>
                        </td>
                        <td className="py-3 pr-3 text-[#6b7280]">{row.book_title}</td>
                        <td className="py-3 pr-3 text-right tabular-nums text-[#6b7280]">{row.days_late_label}</td>
                        <td className="py-3 pr-3 text-right tabular-nums text-[#6b7280]">{row.fine_label}</td>
                        <td className="py-3 pr-5">
                          <StatusPill label={row.status_label} tone={row.status_tone} />
                        </td>
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
              <TablePagination
                pagination={view.pagination}
                onPage={(p) => {
                  setPage(p);
                }}
              />
            </div>
          </section>
        </>
      )}
    </div>
  );
}