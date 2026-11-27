"use client";

import { CollegeAdminModulePageLayout } from "@/features/college-admin/components/layout/college-admin-module-page-layout";
import Link from "next/link";
import { useMemo, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { CollegeAdminPlusActionLabel } from "@/features/college-admin/components/ui/college-admin-plus-action";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { onCollegeAdminMutationError } from "@/features/college-admin/context/college-admin-validation-context";
import { useCreateLmsReportSchedule, useLmsReportsPage } from "@/features/college-admin/hooks/use-lms-reports-settings";
import type { LmsReportsPage, LmsReportsPagination } from "@/features/college-admin/types/lms-reports-settings";
import { cn } from "@/lib/utils";

function TablePagination({
  pagination,
  onPage,
}: {
  pagination: LmsReportsPagination;
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

const emptyPagination: LmsReportsPagination = {
  page: 1,
  page_size: 3,
  total: 0,
  total_pages: 0,
  page_numbers: [],
  has_previous: false,
  has_next: false,
};

function mergeView(data: LmsReportsPage | undefined) {
  return {
    page_title: data?.page_title ?? "",
    page_subtitle: data?.page_subtitle ?? "",
    create_report_label: data?.create_report_label ?? "",
    reports_section_title: data?.reports_section_title ?? "",
    table_headers: data?.table_headers ?? [],
    report_rows: data?.report_rows ?? [],
    create_report_templates: data?.create_report_templates ?? [],
    empty_table_message: data?.empty_table_message ?? "",
    showing_label: data?.showing_label ?? "",
    pagination: data?.pagination ?? emptyPagination,
  };
}

export function LmsReportsDashboard() {
  const [page, setPage] = useState(1);
  const queryParams = useMemo(() => ({ page, page_size: 3 }), [page]);
  const { data, isLoading, isError, error, refetch, isFetching } = useLmsReportsPage(queryParams);
  const view = mergeView(data);
  const createReport = useCreateLmsReportSchedule(queryParams);

  const [showCreate, setShowCreate] = useState(false);
  const [reportKey, setReportKey] = useState("");

  const handleCreate = () => {
    if (!reportKey) {
      toast.error("Select a report type");
      return;
    }
    createReport.mutate(
      { report_key: reportKey },
      {
        onSuccess: () => {
          toast.success("Report scheduled");
          setShowCreate(false);
          setReportKey("");
        },
        onError: onCollegeAdminMutationError,
      },
    );
  };

  return (
    <CollegeAdminModulePageLayout figmaFrame="ca-15-11">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {view.page_title || "LMS Reports"}
          </h2>
          {view.page_subtitle ? (
            <p className="mt-1 text-[14px] text-[#6b7280]">{view.page_subtitle}</p>
          ) : null}
        </div>
        <Button
          type="button"
          className="h-9 shrink-0 gap-1.5 bg-[#245dd8] text-xs font-medium text-white hover:bg-[#1f4fb8]"
          onClick={() => setShowCreate((v) => !v)}
        >
          <CollegeAdminPlusActionLabel label={view.create_report_label || "Create report"} />
        </Button>
      </div>

      {showCreate ? (
        <section className="flex flex-col gap-3 rounded-xl border border-[#e8ecf2] bg-white p-4 shadow-[0_1px_2px_rgba(15,23,42,0.04)] sm:flex-row sm:items-end">
          <div className="min-w-[16rem] flex-1 space-y-1.5">
            <Label className="text-[13px] text-[#374151]">Report type</Label>
            <select
              value={reportKey}
              onChange={(e) => setReportKey(e.target.value)}
              className="h-9 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px] text-[#374151]"
            >
              <option value="">Select…</option>
              {view.create_report_templates.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
          <Button
            type="button"
            className="h-9 bg-[#245dd8] text-xs hover:bg-[#1f4fb8]"
            disabled={createReport.isPending}
            onClick={handleCreate}
          >
            Create
          </Button>
        </section>
      ) : null}

      {isLoading || isFetching ? (
        <p className="text-[12px] text-[#9ca3af]">{isLoading ? "Loading reports…" : "Updating…"}</p>
      ) : null}

      {isError ? (
        <QueryState isError={isError} error={error} onRetry={() => void refetch()}>
          <></>
        </QueryState>
      ) : !isError ? (
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
                    <tr key={row.report_key} className="text-[#374151] hover:bg-[#f9fafb]">
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
                      {view.empty_table_message || "No reports to show."}
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
      ) : null}
    </CollegeAdminModulePageLayout>
  );
}