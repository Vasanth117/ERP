"use client";

import { CollegeAdminModulePageLayout } from "@/features/college-admin/components/layout/college-admin-module-page-layout";
import Link from "next/link";
import { useCallback, useMemo, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { CircleCheckIcon } from "@/components/icons/erp/generated/circle-check";
import { Button } from "@/components/ui/button";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useLmsFacultyContentApproveSelected,
  useLmsFacultyContentManagementPage,
} from "@/features/college-admin/hooks/use-lms-progress-faculty";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import type { PoliciesPagination } from "@/features/college-admin/types/institution";
import { cn } from "@/lib/utils";

function TablePagination({
  pagination,
  onPage,
}: {
  pagination: PoliciesPagination;
  onPage: (page: number) => void;
}) {
  if (pagination.total_pages <= 0) return null;
  return (
    <nav className="flex flex-wrap items-center justify-end gap-1" aria-label="Faculty content pagination">
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

export function LmsFacultyContentManagementDashboard() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const queryParams = useMemo(() => ({ page, page_size: 3 }), [page]);
  const { data, isLoading, isError, error, refetch, isFetching } = useLmsFacultyContentManagementPage(queryParams);
  const approve = useLmsFacultyContentApproveSelected();

  const invalidate = useCallback(() => {
    void queryClient.invalidateQueries({ queryKey: collegeAdminQueryKeys.lmsFacultyContentManagementPage() });
    void queryClient.invalidateQueries({ queryKey: collegeAdminQueryKeys.lmsLearningMaterialManagementPage() });
    void queryClient.invalidateQueries({ queryKey: collegeAdminQueryKeys.lmsVideoLectureManagementPage() });
  }, [queryClient]);

  const handleApprove = useCallback(() => {
    approve.mutate(undefined, { onSuccess: invalidate });
  }, [approve, invalidate]);

  return (
    <CollegeAdminModulePageLayout figmaFrame="161:12312">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Faculty Content Management"}
          </h2>
          {data?.page_subtitle ? <p className="mt-1 text-[14px] text-[#6b7280]">{data.page_subtitle}</p> : null}
        </div>
        <Button
          type="button"
          className="h-9 bg-[#245dd8] text-xs hover:bg-[#1f4fb8]"
          disabled={!data?.approve_selected_enabled || approve.isPending}
          onClick={handleApprove}
        >
          <CircleCheckIcon className="mr-1.5 size-3.5" aria-hidden />
          {data?.approve_selected_action_label ?? "Approve selected"}
        </Button>
      </div>

      {isLoading || isFetching ? (
        <p className="text-[12px] text-[#9ca3af]">{isLoading ? "Loading faculty content…" : "Updating…"}</p>
      ) : null}

      {isError ? (
        <QueryState isError={isError} error={error} onRetry={() => void refetch()}>
          <></>
        </QueryState>
      ) : !data ? null : (
        <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
          <div className="border-b border-[#f1f5f9] px-5 py-3.5">
            <h3 className="text-[14px] font-semibold text-[#111827]">{data.faculty_section_title}</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[48rem] text-left text-[13px]">
              <thead>
                <tr className="border-b border-[#f1f5f9] bg-[#f9fafb] text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                  {data.table_headers.map((header, index, headers) => (
                    <th
                      key={header}
                      className={cn(
                        "pb-3 pt-3 font-medium",
                        index === 0 ? "pl-5 pr-3" : "pr-3",
                        index === headers.length - 1 ? "pr-5" : "",
                        header !== "Faculty" && header !== "Department" ? "text-right tabular-nums" : "",
                      )}
                    >
                      {header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#f1f5f9]">
                {data.faculty_rows.length ? (
                  data.faculty_rows.map((row) => (
                    <tr key={row.row_key} className="text-[#374151] hover:bg-[#f9fafb]">
                      <td className="max-w-[14rem] truncate pl-5 py-3 pr-3 font-medium">
                        <Link href={row.detail_href} className="text-[#245dd8] hover:underline">
                          {row.faculty_label}
                        </Link>
                      </td>
                      <td className="py-3 pr-3 text-[#6b7280]">{row.department_label}</td>
                      <td className="py-3 pr-3 text-right tabular-nums">{row.materials_count}</td>
                      <td className="py-3 pr-3 text-right tabular-nums">{row.videos_count}</td>
                      <td className="py-3 pr-5 text-right tabular-nums font-medium">{row.pending_review_count}</td>
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
            <span>{data.count_footer_label}</span>
            <TablePagination pagination={data.pagination ?? emptyPagination} onPage={setPage} />
          </div>
        </section>
      )}
    </CollegeAdminModulePageLayout>
  );
}