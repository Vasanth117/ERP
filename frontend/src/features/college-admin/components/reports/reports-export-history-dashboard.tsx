"use client";

import { useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { CollegeAdminDownload } from "@/features/college-admin/components/layout/college-admin-erp-icons";
import {
  ReportsStatusPill,
  ReportsTablePagination,
} from "@/features/college-admin/components/reports/reports-table-pagination";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useReportsExportHistoryPage } from "@/features/college-admin/hooks/use-reports-custom-scheduled";
import { cn } from "@/lib/utils";

export function ReportsExportHistoryDashboard() {
  const [page, setPage] = useState(1);
  const params = useMemo(() => ({ page, page_size: 3 }), [page]);
  const { data, isLoading, isError, error, refetch, isFetching } = useReportsExportHistoryPage(params);

  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Export & Download History"}
          </h2>
          {data?.page_subtitle ? <p className="mt-1 text-[14px] text-[#6b7280]">{data.page_subtitle}</p> : null}
        </div>
        <Button
          type="button"
          variant="outline"
          className="h-9 gap-1.5 border-[#dce3ec] text-xs font-medium text-[#374151]"
          onClick={() => void refetch()}
        >
          <CollegeAdminDownload className="h-4 w-4" />
          {data?.export_log_label ?? "Export log"}
        </Button>
      </div>

      {isLoading || isFetching ? (
        <p className="text-[12px] text-[#9ca3af]">{isLoading ? "Loading…" : "Updating…"}</p>
      ) : null}

      <QueryState isError={isError} error={error} onRetry={() => void refetch()}>
        <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
          <div className="border-b border-[#f1f5f9] px-5 py-3.5">
            <h3 className="text-[14px] font-semibold text-[#111827]">{data?.exports_section_title ?? "Exports"}</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[48rem] text-left text-[13px]">
              <thead>
                <tr className="border-b border-[#f1f5f9] text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                  {(data?.table_headers ?? []).map((header, index, headers) => (
                    <th
                      key={header}
                      className={cn(
                        "pb-3 pt-4 font-medium",
                        index === 0 ? "pl-5 pr-3" : "px-3",
                        index === headers.length - 1 ? "pr-5 text-right" : "",
                      )}
                    >
                      {header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#f1f5f9]">
                {data?.export_rows?.length ? (
                  data.export_rows.map((row) => (
                    <tr key={row.row_key} className="text-[#374151] hover:bg-[#f9fafb]">
                      <td className="py-3 pl-5 pr-3 font-medium text-[#111827]">{row.file_label}</td>
                      <td className="px-3 py-3 text-[#6b7280]">{row.requested_by_label}</td>
                      <td className="px-3 py-3 text-[#6b7280]">{row.format_label}</td>
                      <td className="px-3 py-3 tabular-nums text-[#6b7280]">{row.size_label}</td>
                      <td className="px-3 py-3 tabular-nums text-[#6b7280]">{row.date_label}</td>
                      <td className="py-3 pl-3 pr-5 text-right">
                        <ReportsStatusPill label={row.status_label} tone={row.status_tone} />
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={Math.max(data?.table_headers?.length ?? 1, 1)} className="px-5 py-10 text-center text-sm text-[#9ca3af]">
                      {data?.empty_table_message ?? "No exports to show."}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
            <span>{data?.showing_label ?? ""}</span>
            {data?.pagination ? <ReportsTablePagination pagination={data.pagination} onPage={setPage} /> : null}
          </div>
        </section>
      </QueryState>
    </div>
  );
}