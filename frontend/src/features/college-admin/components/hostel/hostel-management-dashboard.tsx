"use client";

import { CollegeAdminModulePageLayout } from "@/features/college-admin/components/layout/college-admin-module-page-layout";
import Link from "next/link";
import { useMemo, useState } from "react";

import { CollegeAdminPlusActionLabel } from "@/features/college-admin/components/ui/college-admin-plus-action";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useHostelManagementPage } from "@/features/college-admin/hooks/use-hostel-management-page";
import type { HostelManagementPage } from "@/features/college-admin/types/hostel-management-page";
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

function mergeView(data: HostelManagementPage | undefined) {
  return {
    figma_frame: data?.figma_frame ?? "",
    page_title: data?.page_title ?? "",
    page_subtitle: data?.page_subtitle ?? "",
    primary_action_label: data?.primary_action_label ?? "",
    primary_action_href: data?.primary_action_href ?? "#",
    section_title: data?.section_title ?? "",
    count_label: data?.count_label ?? "",
    table_headers: data?.table_headers ?? [],
    rows: data?.rows ?? [],
    empty_table_message: data?.empty_table_message ?? "",
    showing_label: data?.showing_label ?? "",
    pagination: data?.pagination,
  };
}

export function HostelManagementDashboard({ screenSlug }: { screenSlug: string }) {
  const [page, setPage] = useState(1);
  const queryParams = useMemo(() => ({ page, page_size: 8 }), [page]);
  const { data, isLoading, isError, error, refetch, isFetching } = useHostelManagementPage(
    screenSlug,
    queryParams,
  );
  const view = mergeView(data);

  return (
    <CollegeAdminModulePageLayout figmaFrame={view.figma_frame || undefined}>
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {view.page_title || "Hostel"}
          </h2>
          {view.page_subtitle ? (
            <p className="mt-1 text-[14px] text-[#6b7280]">{view.page_subtitle}</p>
          ) : null}
        </div>
        {view.primary_action_label ? (
          <Link
            href={view.primary_action_href}
            className="inline-flex h-9 shrink-0 items-center rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
          >
            <CollegeAdminPlusActionLabel label={view.primary_action_label} />
          </Link>
        ) : null}
      </div>

      {isLoading || isFetching ? (
        <p className="text-[12px] text-[#9ca3af]">{isLoading ? "Loading…" : "Updating…"}</p>
      ) : null}

      <QueryState
        isLoading={isLoading && !data}
        isError={isError}
        error={error}
        onRetry={() => void refetch()}
      >
        <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
          <div className="flex items-center justify-between border-b border-[#f1f5f9] px-5 py-3.5">
            <h3 className="text-[14px] font-semibold text-[#111827]">{view.section_title || "Records"}</h3>
            <span className="text-[12px] text-[#9ca3af]">{view.count_label}</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[40rem] text-left text-[13px]">
              <thead>
                <tr className="border-b border-[#f1f5f9] text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                  {view.table_headers.map((header, index, headers) => (
                    <th
                      key={header}
                      className={cn(
                        "pb-3 pt-4 font-medium",
                        index === 0 ? "pl-5 pr-3" : "pr-3",
                        index === headers.length - 1 ? "pr-5" : "",
                      )}
                    >
                      {header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#f1f5f9]">
                {view.rows.length ? (
                  view.rows.map((row) => (
                    <tr key={row.row_id} className="text-[#374151] hover:bg-[#f9fafb]">
                      {row.cells.map((cell, cellIndex) => (
                        <td
                          key={`${row.row_id}-${cellIndex}`}
                          className={cn("py-3 pr-3", cellIndex === 0 ? "pl-5 font-medium text-[#111827]" : "")}
                        >
                          {cellIndex === 0 && row.detail_href ? (
                            <Link href={row.detail_href} className="hover:text-[#245dd8]">
                              {cell}
                            </Link>
                          ) : cellIndex === row.cells.length - 1 && row.status_label ? (
                            <StatusPill label={row.status_label} tone={row.status_tone || "muted"} />
                          ) : (
                            cell
                          )}
                        </td>
                      ))}
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td
                      colSpan={Math.max(view.table_headers.length, 1)}
                      className="px-5 py-10 text-center text-[13px] text-[#6b7280]"
                    >
                      {view.empty_table_message || "No records to display."}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          <div className="flex flex-wrap items-center justify-between gap-3 border-t border-[#f1f5f9] px-5 py-3">
            <span className="text-[12px] text-[#9ca3af]">{view.showing_label}</span>
            {view.pagination && view.pagination.total_pages > 1 ? (
              <nav className="flex flex-wrap items-center gap-1" aria-label="Table pagination">
                <button
                  type="button"
                  className="rounded border border-[#dce3ec] px-2 py-1 text-[12px] disabled:opacity-40"
                  disabled={!view.pagination.has_previous}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                >
                  ‹
                </button>
                <span className="px-2 text-[12px] text-[#6b7280]">
                  {view.pagination.page} / {view.pagination.total_pages}
                </span>
                <button
                  type="button"
                  className="rounded border border-[#dce3ec] px-2 py-1 text-[12px] disabled:opacity-40"
                  disabled={!view.pagination.has_next}
                  onClick={() => setPage((p) => p + 1)}
                >
                  ›
                </button>
              </nav>
            ) : null}
          </div>
        </section>
      </QueryState>
    </CollegeAdminModulePageLayout>
  );
}