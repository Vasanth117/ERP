"use client";

import { CollegeAdminModulePageLayout } from "@/features/college-admin/components/layout/college-admin-module-page-layout";
import Link from "next/link";
import { useCallback, useMemo, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { CircleCheckIcon } from "@/components/icons/erp/generated/circle-check";
import { RefreshCwIcon } from "@/components/icons/erp/generated/refresh-cw";
import { TriangleAlertIcon } from "@/components/icons/erp/generated/triangle-alert";
import { Button } from "@/components/ui/button";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useLmsSubjectAutoMap,
  useLmsSubjectCourseMappingPage,
  useLmsSubjectSaveMapping,
} from "@/features/college-admin/hooks/use-lms-courses-mapping";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { LmsChannelAlertBanner, LmsSubjectCourseMappingPage } from "@/features/college-admin/types/lms-courses-mapping";
import type { PoliciesPagination } from "@/features/college-admin/types/institution";
import { cn } from "@/lib/utils";

function StatusPill({ label, tone }: { label: string; tone: string }) {
  const styles: Record<string, string> = {
    success: "bg-[#ecfdf5] text-[#047857]",
    warning: "bg-[#fff7ed] text-[#c2410c]",
    muted: "bg-[#f3f4f6] text-[#6b7280]",
  };
  const dot: Record<string, string> = {
    success: "bg-[#10b981]",
    warning: "bg-[#f97316]",
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

function MappingAlertBanner({ alert }: { alert: LmsChannelAlertBanner }) {
  const bg = alert.tone === "warning" ? "border-[#fde68a] bg-[#fffbeb]" : "border-[#bfdbfe] bg-[#eff6ff]";
  return (
    <div className={cn("flex gap-3 rounded-lg border px-4 py-3", bg)}>
      <TriangleAlertIcon className="mt-0.5 size-5 shrink-0 text-[#d97706]" aria-hidden />
      <div className="min-w-0 space-y-1 text-[13px]">
        <p className="font-semibold text-[#92400e]">{alert.message}</p>
        {alert.link_label ? <p className="text-[#b45309]">{alert.link_label}</p> : null}
      </div>
    </div>
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
    <nav className="flex flex-wrap items-center justify-end gap-1" aria-label="Mapping pagination">
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

function mergeView(data: LmsSubjectCourseMappingPage | undefined) {
  return {
    page_title: data?.page_title ?? "",
    page_subtitle: data?.page_subtitle ?? "",
    auto_map_action_label: data?.auto_map_action_label ?? "",
    save_mapping_action_label: data?.save_mapping_action_label ?? "",
    save_mapping_enabled: data?.save_mapping_enabled ?? false,
    alert_banner: data?.alert_banner ?? null,
    mapping_section_title: data?.mapping_section_title ?? "",
    table_headers: data?.table_headers ?? [],
    mapping_rows: data?.mapping_rows ?? [],
    empty_table_message: data?.empty_table_message ?? "",
    count_footer_label: data?.count_footer_label ?? "",
    pagination: data?.pagination ?? emptyPagination,
  };
}

export function LmsSubjectCourseMappingDashboard() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const queryParams = useMemo(() => ({ page, page_size: 3 }), [page]);

  const { data, isLoading, isError, error, refetch, isFetching } = useLmsSubjectCourseMappingPage(queryParams);
  const autoMap = useLmsSubjectAutoMap();
  const saveMapping = useLmsSubjectSaveMapping();
  const view = mergeView(data);

  const invalidate = useCallback(() => {
    void queryClient.invalidateQueries({ queryKey: collegeAdminQueryKeys.lmsSubjectCourseMappingPage() });
    void queryClient.invalidateQueries({ queryKey: collegeAdminQueryKeys.lmsCourseManagementPage() });
  }, [queryClient]);

  const handleAutoMap = useCallback(() => {
    autoMap.mutate(undefined, { onSuccess: invalidate });
  }, [autoMap, invalidate]);

  const handleSave = useCallback(() => {
    saveMapping.mutate(undefined, { onSuccess: invalidate });
  }, [saveMapping, invalidate]);

  const actionsBusy = autoMap.isPending || saveMapping.isPending;

  return (
    <CollegeAdminModulePageLayout figmaFrame="161:11719">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {view.page_title || "Subject & Course Mapping"}
          </h2>
          {view.page_subtitle ? (
            <p className="mt-1 text-[14px] text-[#6b7280]">{view.page_subtitle}</p>
          ) : null}
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            type="button"
            variant="outline"
            className="h-9 border-[#dce3ec] bg-white text-xs text-[#374151]"
            disabled={actionsBusy}
            onClick={handleAutoMap}
          >
            <RefreshCwIcon className={cn("mr-1.5 size-3.5", actionsBusy ? "animate-spin" : "")} aria-hidden />
            {view.auto_map_action_label || "Auto map"}
          </Button>
          <Button
            type="button"
            className="h-9 bg-[#245dd8] text-xs hover:bg-[#1f4fb8]"
            disabled={!view.save_mapping_enabled || actionsBusy}
            onClick={handleSave}
          >
            <CircleCheckIcon className="mr-1.5 size-3.5" aria-hidden />
            {view.save_mapping_action_label || "Save mapping"}
          </Button>
        </div>
      </div>

      {isLoading || isFetching ? (
        <p className="text-[12px] text-[#9ca3af]">{isLoading ? "Loading mapping…" : "Updating…"}</p>
      ) : null}

      {isError ? (
        <QueryState isError={isError} error={error} onRetry={() => void refetch()}>
          <></>
        </QueryState>
      ) : !data ? null : (
        <>
          {view.alert_banner ? <MappingAlertBanner alert={view.alert_banner} /> : null}

          <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
            <div className="border-b border-[#f1f5f9] px-5 py-3.5">
              <h3 className="text-[14px] font-semibold text-[#111827]">{view.mapping_section_title}</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[48rem] text-left text-[13px]">
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
                  {view.mapping_rows.length ? (
                    view.mapping_rows.map((row) => (
                      <tr key={row.row_key} className="text-[#374151] hover:bg-[#f9fafb]">
                        <td className="max-w-[14rem] truncate pl-5 py-3 pr-3 font-medium text-[#111827]">
                          <Link href={row.detail_href} className="hover:text-[#245dd8] hover:underline">
                            {row.subject_label}
                          </Link>
                        </td>
                        <td className="py-3 pr-3 text-[#6b7280]">{row.section_label}</td>
                        <td className="py-3 pr-3 text-[#6b7280]">{row.faculty_label}</td>
                        <td className="py-3 pr-3 tabular-nums text-[#374151]">{row.lms_course_label}</td>
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
              <span>{view.count_footer_label}</span>
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
    </CollegeAdminModulePageLayout>
  );
}