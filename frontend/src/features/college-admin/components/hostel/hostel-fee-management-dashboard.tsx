"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import {
  CollegeAdminKpiGrid,
  CollegeAdminUserDashboardKpiCard,
} from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { CollegeAdminPlusActionLabel } from "@/features/college-admin/components/ui/college-admin-plus-action";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useHostelFeeManagementPage } from "@/features/college-admin/hooks/use-hostel-fee-management";
import type {
  HostelFeeManagementPage,
  HostelFeeManagementPagination,
} from "@/features/college-admin/types/hostel-fee-management";
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
  pagination: HostelFeeManagementPagination;
  onPage: (page: number) => void;
}) {
  if (pagination.total_pages <= 1) return null;
  return (
    <nav className="flex flex-wrap items-center justify-end gap-1" aria-label="Hostel fees pagination">
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

const emptyPagination: HostelFeeManagementPagination = {
  page: 1,
  page_size: 3,
  total: 0,
  total_pages: 0,
  page_numbers: [],
  has_previous: false,
  has_next: false,
};

function mergeView(data: HostelFeeManagementPage | undefined) {
  return {
    page_title: data?.page_title ?? "",
    page_subtitle: data?.page_subtitle ?? "",
    generate_fees_label: data?.generate_fees_label ?? "",
    generate_fees_href: data?.generate_fees_href ?? "#",
    kpis: data?.kpis ?? [],
    fees_section_title: data?.fees_section_title ?? "",
    table_headers: data?.table_headers ?? [],
    fee_rows: data?.fee_rows ?? [],
    empty_table_message: data?.empty_table_message ?? "",
    count_label: data?.count_label ?? "",
    showing_label: data?.showing_label ?? "",
    pagination: data?.pagination ?? emptyPagination,
  };
}

export function HostelFeeManagementDashboard() {
  const [page, setPage] = useState(1);
  const queryParams = useMemo(() => ({ page, page_size: 3 }), [page]);
  const { data, isLoading, isError, error, refetch, isFetching } = useHostelFeeManagementPage(queryParams);
  const view = mergeView(data);

  return (
    <div className="space-y-5" data-figma-frame="161:4530">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {view.page_title || "Hostel Fee Management"}
          </h2>
          {view.page_subtitle ? (
            <p className="mt-1 text-[14px] text-[#6b7280]">{view.page_subtitle}</p>
          ) : null}
        </div>
        <Link
          href={view.generate_fees_href}
          className="inline-flex h-9 shrink-0 items-center rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
        >
          <CollegeAdminPlusActionLabel label={view.generate_fees_label || "Generate fees"} />
        </Link>
      </div>

      {isLoading || isFetching ? (
        <p className="text-[12px] text-[#9ca3af]">{isLoading ? "Loading fees…" : "Updating…"}</p>
      ) : null}

      <QueryState
        isLoading={isLoading && !data}
        isError={isError}
        error={error}
        onRetry={() => void refetch()}
      >
        <>
          <CollegeAdminKpiGrid>
            {view.kpis.map((kpi, index) => (
              <CollegeAdminUserDashboardKpiCard key={kpi.key} kpi={kpi} index={index} />
            ))}
          </CollegeAdminKpiGrid>

          <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
            <div className="border-b border-[#f1f5f9] px-5 py-3.5">
              <h3 className="text-[14px] font-semibold text-[#111827]">
                {view.fees_section_title || "Hostel fees"}
              </h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[52rem] text-left text-[13px]">
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
                  {view.fee_rows.length ? (
                    view.fee_rows.map((row) => (
                      <tr key={row.row_key} className="text-[#374151] hover:bg-[#f9fafb]">
                        <td className="pl-5 py-3 pr-3 font-semibold text-[#111827]">
                          <Link href={row.detail_href} className="hover:text-[#245dd8]">
                            {row.resident_label}
                          </Link>
                        </td>
                        <td className="py-3 pr-3 tabular-nums text-[#6b7280]">{row.room_label}</td>
                        <td className="py-3 pr-3 text-right tabular-nums">{row.billed_label}</td>
                        <td className="py-3 pr-3 text-right tabular-nums text-[#6b7280]">{row.paid_label}</td>
                        <td className="py-3 pr-3 text-right tabular-nums font-medium text-[#111827]">
                          {row.balance_label}
                        </td>
                        <td className="py-3 pr-5 text-right">
                          <StatusPill label={row.status_label} tone={row.status_tone} />
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td
                        colSpan={Math.max(view.table_headers.length, 1)}
                        className="px-5 py-10 text-center text-[13px] text-[#6b7280]"
                      >
                        {view.empty_table_message}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
            <div className="flex flex-wrap items-center justify-between gap-3 border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
              <span>{view.count_label || view.showing_label}</span>
              <TablePagination pagination={view.pagination} onPage={setPage} />
            </div>
          </section>
        </>
      </QueryState>
    </div>
  );
}