"use client";

import { CollegeAdminModulePageLayout } from "@/features/college-admin/components/layout/college-admin-module-page-layout";
import Link from "next/link";
import { useCallback, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { CollegeAdminDownload } from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useHostelLeaveOutpassApprovalPage } from "@/features/college-admin/hooks/use-hostel-leave-outpass-approval";
import type {
  HostelLeaveOutpassApprovalPage,
  HostelLeaveOutpassApprovalPagination,
} from "@/features/college-admin/types/hostel-leave-outpass-approval";
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
  pagination: HostelLeaveOutpassApprovalPagination;
  onPage: (page: number) => void;
}) {
  if (pagination.total_pages <= 1) return null;
  return (
    <nav className="flex flex-wrap items-center justify-end gap-1" aria-label="Outpass pagination">
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

const emptyPagination: HostelLeaveOutpassApprovalPagination = {
  page: 1,
  page_size: 4,
  total: 0,
  total_pages: 0,
  page_numbers: [],
  has_previous: false,
  has_next: false,
};

function mergeView(data: HostelLeaveOutpassApprovalPage | undefined) {
  return {
    page_title: data?.page_title ?? "",
    page_subtitle: data?.page_subtitle ?? "",
    export_label: data?.export_label ?? "",
    outpass_section_title: data?.outpass_section_title ?? "",
    table_headers: data?.table_headers ?? [],
    outpass_rows: data?.outpass_rows ?? [],
    empty_table_message: data?.empty_table_message ?? "",
    showing_label: data?.showing_label ?? "",
    pagination: data?.pagination ?? emptyPagination,
  };
}

export function HostelLeaveOutpassApprovalDashboard() {
  const [page, setPage] = useState(1);
  const queryParams = useMemo(() => ({ page, page_size: 4 }), [page]);
  const { data, isLoading, isError, error, refetch, isFetching } =
    useHostelLeaveOutpassApprovalPage(queryParams);
  const view = mergeView(data);

  const handleExport = useCallback(() => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `hostel-outpass-${new Date(data.generated_at).toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data]);

  return (
    <CollegeAdminModulePageLayout figmaFrame="161:5435">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {view.page_title || "Leave & Outpass Approval"}
          </h2>
          {view.page_subtitle ? (
            <p className="mt-1 text-[14px] text-[#6b7280]">{view.page_subtitle}</p>
          ) : null}
        </div>
        <Button
          type="button"
          className="h-9 gap-1.5 bg-[#245dd8] text-xs font-medium text-white hover:bg-[#1f4fb8]"
          onClick={handleExport}
          disabled={isLoading || !data}
        >
          <CollegeAdminDownload className="size-3.5" aria-hidden />
          {view.export_label || "Export"}
        </Button>
      </div>

      {isLoading || isFetching ? (
        <p className="text-[12px] text-[#9ca3af]">{isLoading ? "Loading outpass requests…" : "Updating…"}</p>
      ) : null}

      <QueryState
        isLoading={isLoading && !data}
        isError={isError}
        error={error}
        onRetry={() => void refetch()}
      >
        <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
          <div className="border-b border-[#f1f5f9] px-5 py-3.5">
            <h3 className="text-[14px] font-semibold text-[#111827]">
              {view.outpass_section_title || "Outpass requests"}
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
                      )}
                    >
                      {header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#f1f5f9]">
                {view.outpass_rows.length ? (
                  view.outpass_rows.map((row) => (
                    <tr key={row.request_id} className="text-[#374151] hover:bg-[#f9fafb]">
                      <td className="pl-5 py-3 pr-3 font-medium text-[#111827]">
                        <Link href={row.detail_href} className="hover:text-[#245dd8]">
                          {row.resident_label}
                        </Link>
                      </td>
                      <td className="py-3 pr-3">{row.type_label}</td>
                      <td className="py-3 pr-3 text-[#6b7280]">{row.from_label}</td>
                      <td className="py-3 pr-3 text-[#6b7280]">{row.to_label}</td>
                      <td className="py-3 pr-3">
                        <StatusPill label={row.guardian_label} tone={row.guardian_tone} />
                      </td>
                      <td className="py-3 pr-5">
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
            <span>{view.showing_label}</span>
            <TablePagination pagination={view.pagination} onPage={setPage} />
          </div>
        </section>
      </QueryState>
    </CollegeAdminModulePageLayout>
  );
}