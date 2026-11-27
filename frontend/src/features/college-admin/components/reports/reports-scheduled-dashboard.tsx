"use client";

import { useMemo, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { CollegeAdminPlusActionLabel } from "@/features/college-admin/components/ui/college-admin-plus-action";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { onCollegeAdminMutationError } from "@/features/college-admin/context/college-admin-validation-context";
import {
  ReportsStatusPill,
  ReportsTablePagination,
} from "@/features/college-admin/components/reports/reports-table-pagination";
import { useCreateReportsSchedule, useReportsScheduledPage } from "@/features/college-admin/hooks/use-reports-custom-scheduled";
import { cn } from "@/lib/utils";

export function ReportsScheduledDashboard() {
  const [page, setPage] = useState(1);
  const params = useMemo(() => ({ page, page_size: 4 }), [page]);
  const { data, isLoading, isError, error, refetch, isFetching } = useReportsScheduledPage(params);
  const createSchedule = useCreateReportsSchedule(params);
  const [showCreate, setShowCreate] = useState(false);
  const [reportKey, setReportKey] = useState("");

  const handleSchedule = () => {
    if (!reportKey) {
      toast.error("Select a report");
      return;
    }
    createSchedule.mutate(
      { report_key: reportKey, frequency_label: "Weekly", export_format: "excel" },
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

  const view = data;

  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {view?.page_title ?? "Scheduled Reports"}
          </h2>
          {view?.page_subtitle ? <p className="mt-1 text-[14px] text-[#6b7280]">{view.page_subtitle}</p> : null}
        </div>
        <Button
          type="button"
          className="h-9 shrink-0 gap-1.5 bg-[#245dd8] text-xs font-medium text-white hover:bg-[#1f4fb8]"
          onClick={() => setShowCreate((v) => !v)}
        >
          <CollegeAdminPlusActionLabel label={view?.schedule_action_label ?? "Schedule report"} />
        </Button>
      </div>

      {showCreate ? (
        <section className="flex flex-col gap-3 rounded-xl border border-[#e8ecf2] bg-white p-4 shadow-[0_1px_2px_rgba(15,23,42,0.04)] sm:flex-row sm:items-end">
          <div className="min-w-[16rem] flex-1 space-y-1.5">
            <Label className="text-[13px] text-[#374151]">Report</Label>
            <select
              value={reportKey}
              onChange={(e) => setReportKey(e.target.value)}
              className="h-9 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px]"
            >
              <option value="">Select…</option>
              {(view?.report_options ?? []).map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
          <Button
            type="button"
            className="h-9 bg-[#245dd8] text-xs hover:bg-[#1f4fb8]"
            disabled={createSchedule.isPending}
            onClick={handleSchedule}
          >
            Schedule
          </Button>
        </section>
      ) : null}

      {isLoading || isFetching ? (
        <p className="text-[12px] text-[#9ca3af]">{isLoading ? "Loading…" : "Updating…"}</p>
      ) : null}

      <QueryState isError={isError} error={error} onRetry={() => void refetch()}>
        <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
          <div className="border-b border-[#f1f5f9] px-5 py-3.5">
            <h3 className="text-[14px] font-semibold text-[#111827]">
              {view?.schedules_section_title ?? "Schedules"}
            </h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[52rem] text-left text-[13px]">
              <thead>
                <tr className="border-b border-[#f1f5f9] text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                  {(view?.table_headers ?? []).map((header, index, headers) => (
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
                {view?.schedule_rows?.length ? (
                  view.schedule_rows.map((row) => (
                    <tr key={row.row_key} className="text-[#374151] hover:bg-[#f9fafb]">
                      <td className="py-3 pl-5 pr-3 font-medium text-[#111827]">{row.report_label}</td>
                      <td className="px-3 py-3 text-[#6b7280]">{row.frequency_label}</td>
                      <td className="px-3 py-3 tabular-nums text-[#6b7280]">{row.next_run_label}</td>
                      <td className="px-3 py-3 text-[#6b7280]">{row.recipients_label}</td>
                      <td className="px-3 py-3 text-[#6b7280]">{row.format_label}</td>
                      <td className="py-3 pl-3 pr-5 text-right">
                        <ReportsStatusPill label={row.status_label} tone={row.status_tone} />
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={Math.max(view?.table_headers?.length ?? 1, 1)} className="px-5 py-10 text-center text-sm text-[#9ca3af]">
                      {view?.empty_table_message ?? "No schedules to show."}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
            <span>{view?.showing_label ?? ""}</span>
            {view?.pagination ? <ReportsTablePagination pagination={view.pagination} onPage={setPage} /> : null}
          </div>
        </section>
      </QueryState>
    </div>
  );
}