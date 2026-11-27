"use client";

import { CollegeAdminModulePageLayout } from "@/features/college-admin/components/layout/college-admin-module-page-layout";
import Link from "next/link";
import { useMemo, useState } from "react";

import { UploadIcon } from "@/components/icons/erp/generated/upload";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useLmsLearningMaterialManagementPage } from "@/features/college-admin/hooks/use-lms-content";
import type { LmsLearningMaterialManagementPage } from "@/features/college-admin/types/lms-content";
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
  pagination: PoliciesPagination;
  onPage: (page: number) => void;
}) {
  if (pagination.total_pages <= 0) return null;
  return (
    <nav className="flex flex-wrap items-center justify-end gap-1" aria-label="Materials pagination">
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

const emptyPagination: PoliciesPagination = {
  page: 1,
  page_size: 3,
  total: 0,
  total_pages: 0,
  page_numbers: [],
  has_previous: false,
  has_next: false,
};

function mergeView(data: LmsLearningMaterialManagementPage | undefined) {
  return {
    page_title: data?.page_title ?? "",
    page_subtitle: data?.page_subtitle ?? "",
    primary_action_label: data?.primary_action_label ?? "",
    primary_action_href: data?.primary_action_href ?? "#",
    materials_section_title: data?.materials_section_title ?? "",
    table_headers: data?.table_headers ?? [],
    material_rows: data?.material_rows ?? [],
    empty_table_message: data?.empty_table_message ?? "",
    showing_label: data?.showing_label ?? "",
    pagination: data?.pagination ?? emptyPagination,
  };
}

export function LmsLearningMaterialManagementDashboard() {
  const [page, setPage] = useState(1);
  const queryParams = useMemo(() => ({ page, page_size: 3 }), [page]);
  const { data, isLoading, isError, error, refetch, isFetching } = useLmsLearningMaterialManagementPage(queryParams);
  const view = mergeView(data);

  return (
    <CollegeAdminModulePageLayout figmaFrame="161:11452">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {view.page_title || "Learning Material Management"}
          </h2>
          {view.page_subtitle ? (
            <p className="mt-1 text-[14px] text-[#6b7280]">{view.page_subtitle}</p>
          ) : null}
        </div>
        <Link
          href={view.primary_action_href}
          className="inline-flex h-9 shrink-0 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
        >
          <UploadIcon className="size-3.5" aria-hidden />
          {view.primary_action_label || "Upload material"}
        </Link>
      </div>

      {isLoading || isFetching ? (
        <p className="text-[12px] text-[#9ca3af]">{isLoading ? "Loading materials…" : "Updating…"}</p>
      ) : null}

      {isError ? (
        <QueryState isError={isError} error={error} onRetry={() => void refetch()}>
          <></>
        </QueryState>
      ) : !data ? null : (
        <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
          <div className="border-b border-[#f1f5f9] px-5 py-3.5">
            <h3 className="text-[14px] font-semibold text-[#111827]">{view.materials_section_title}</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[52rem] text-left text-[13px]">
              <thead>
                <tr className="border-b border-[#f1f5f9] bg-[#f9fafb] text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                  {view.table_headers.map((header, index, headers) => (
                    <th
                      key={header}
                      className={cn(
                        "pb-3 pt-3 font-medium",
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
                {view.material_rows.length ? (
                  view.material_rows.map((row) => (
                    <tr key={row.row_key} className="text-[#374151] hover:bg-[#f9fafb]">
                      <td className="max-w-[16rem] truncate pl-5 py-3 pr-3 font-medium text-[#111827]">
                        <Link href={row.detail_href} className="text-[#245dd8] hover:underline">
                          {row.material_label}
                        </Link>
                      </td>
                      <td className="py-3 pr-3 tabular-nums text-[#6b7280]">{row.course_code}</td>
                      <td className="py-3 pr-3 text-[#6b7280]">{row.type_label}</td>
                      <td className="py-3 pr-3 text-[#6b7280]">{row.uploaded_by_label}</td>
                      <td className="py-3 pr-3 text-[#6b7280]">{row.date_label}</td>
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
            <TablePagination pagination={view.pagination} onPage={setPage} />
          </div>
        </section>
      )}
    </CollegeAdminModulePageLayout>
  );
}