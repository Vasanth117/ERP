"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { CollegeAdminPlusActionLabel } from "@/features/college-admin/components/ui/college-admin-plus-action";
import { HrRecruitmentSubNav } from "@/features/college-admin/components/hr/hr-recruitment-sub-nav";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { onCollegeAdminMutationError } from "@/features/college-admin/context/college-admin-validation-context";
import { useCreateHrReportSchedule, useHrReportsPage } from "@/features/college-admin/hooks/use-hr-reports-settings";
import type { HrReportsPage } from "@/features/college-admin/types/hr-reports-settings";
import type { HrRecruitmentPagination, HrRecruitmentSubNavItem } from "@/features/college-admin/types/hr-recruitment";
import { cn } from "@/lib/utils";

const DEFAULT_SUB_NAV: HrRecruitmentSubNavItem[] = [
  { key: "hr-reports", label: "HR reports", href: "/college-admin/hr/hr-reports" },
  { key: "settings-policies", label: "HR settings & policies", href: "/college-admin/hr/hr-settings-policies" },
];

const TABLE_HEADERS = ["Report", "Period", "Format", "Last run", "Schedule"];

function TablePagination({
  pagination,
  onPage,
}: {
  pagination: HrRecruitmentPagination;
  onPage: (page: number) => void;
}) {
  if (pagination.total_pages <= 0) return null;
  return (
    <div className="flex items-center gap-1">
      <button
        type="button"
        className="rounded border border-[#dce3ec] px-2 py-1 disabled:opacity-40"
        disabled={!pagination.has_previous}
        onClick={() => onPage(Math.max(1, pagination.page - 1))}
      >
        ‹
      </button>
      {pagination.page_numbers.map((num, index) =>
        num === -1 ? (
          <span key={`ellipsis-${index}`} className="px-1">
            …
          </span>
        ) : (
          <button
            key={num}
            type="button"
            className={cn(
              "min-w-8 rounded border px-2 py-1 tabular-nums",
              num === pagination.page ? "border-[#245dd8] bg-[#eff6ff] text-[#245dd8]" : "border-[#dce3ec]",
            )}
            onClick={() => onPage(num)}
          >
            {num}
          </button>
        ),
      )}
    </div>
  );
}

function mergeView(data: HrReportsPage | undefined) {
  const emptyPagination: HrRecruitmentPagination = {
    page: 1,
    page_size: 4,
    total: 0,
    total_pages: 0,
    page_numbers: [],
    has_previous: false,
    has_next: false,
  };
  return {
    page_title: data?.page_title ?? "HR Reports",
    page_subtitle: data?.page_subtitle ?? "Standard HR reports",
    create_report_label: data?.create_report_label ?? "Create report",
    sub_nav: data?.sub_nav?.length ? data.sub_nav : DEFAULT_SUB_NAV,
    reports_section_title: data?.reports_section_title ?? "Reports",
    table_headers: data?.table_headers?.length ? data.table_headers : TABLE_HEADERS,
    report_rows: data?.report_rows ?? [],
    create_report_templates: data?.create_report_templates ?? [],
    showing_label: data?.showing_label ?? "0 of 0",
    pagination: data?.pagination ?? emptyPagination,
    footer_disclaimer: data?.footer_disclaimer ?? "",
    footer_snapshot_label: data?.footer_snapshot_label ?? "",
  };
}

export function HrReportsDashboard() {
  const [page, setPage] = useState(1);
  const queryParams = useMemo(() => ({ page, page_size: 4 }), [page]);
  const { data, isLoading, isError, error, refetch, isFetching } = useHrReportsPage(queryParams);
  const view = mergeView(data);
  const createReport = useCreateHrReportSchedule(queryParams);

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
    <div className="space-y-5" data-figma-frame="160:10983">
      <HrRecruitmentSubNav items={view.sub_nav} />

      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">{view.page_title}</h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">{view.page_subtitle}</p>
        </div>
        <Button
          type="button"
          className="h-9 shrink-0 gap-1.5 bg-[#245dd8] text-xs font-medium text-white hover:bg-[#1f4fb8]"
          onClick={() => setShowCreate((v) => !v)}
        >
          <CollegeAdminPlusActionLabel iconClassName="size-3.5" label={view.create_report_label} />
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

      {isError ? <QueryState isError={isError} error={error} onRetry={() => void refetch()} /> : null}

      {!isError ? (
        <>
          <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
            <div className="border-b border-[#f1f5f9] px-5 py-3.5">
              <h3 className="text-[14px] font-semibold text-[#111827]">{view.reports_section_title}</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[44rem] text-left text-[13px]">
                <thead>
                  <tr className="border-b border-[#f1f5f9] text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                    {view.table_headers.map((header, index) => (
                      <th
                        key={header}
                        className={cn(
                          "pb-3 pt-4 font-medium",
                          index === 0 ? "pl-5 pr-3" : "pr-3",
                          index === view.table_headers.length - 1 ? "pr-5" : "",
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
                      <tr key={row.row_id} className="hover:bg-[#f9fafb]">
                        <td className="pl-5 py-3 pr-3 font-medium text-[#111827]">
                          <Link href={row.detail_href} className="hover:text-[#245dd8]">
                            {row.report_label}
                          </Link>
                        </td>
                        <td className="py-3 pr-3 text-[#374151]">{row.period_label}</td>
                        <td className="py-3 pr-3 text-[#374151]">{row.format_label}</td>
                        <td className="py-3 pr-3 text-[#6b7280]">{row.last_run_label}</td>
                        <td className="py-3 pr-5 text-[#374151]">{row.schedule_label}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={view.table_headers.length} className="px-5 py-10 text-center text-sm text-[#9ca3af]">
                        No scheduled reports yet. Use Create report to add one from the HR catalogue.
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

          <footer className="flex flex-col gap-1 text-[11px] text-[#9ca3af] sm:flex-row sm:items-center sm:justify-between">
            <p>{view.footer_disclaimer}</p>
            {view.footer_snapshot_label ? <p>{view.footer_snapshot_label}</p> : null}
          </footer>
        </>
      ) : null}
    </div>
  );
}