"use client";

import { useState } from "react";

import { CircleAlertIcon } from "@/components/icons/erp/generated/circle-alert";
import { Button } from "@/components/ui/button";
import {
  CollegeAdminKpiGrid,
  CollegeAdminUserDashboardKpiCard,
} from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useAttendanceMonitoringPage,
  useNotifyFacultyMissingAttendance,
} from "@/features/college-admin/hooks/use-attendance-monitoring";
import { cn } from "@/lib/utils";

function ActionBadge({ label, tone }: { label: string; tone: string }) {
  const styles: Record<string, string> = {
    warning: "bg-[#fff7ed] text-[#c2410c]",
    info: "bg-[#eff6ff] text-[#1d4ed8]",
    error: "bg-[#fef2f2] text-[#b91c1c]",
    muted: "bg-[#f3f4f6] text-[#6b7280]",
  };
  const dot: Record<string, string> = {
    warning: "bg-[#f97316]",
    info: "bg-[#3b82f6]",
    error: "bg-[#ef4444]",
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

export function AttendanceMonitoringDashboard() {
  const [page, setPage] = useState(1);
  const queryParams = { page, page_size: 10 };
  const { data, isLoading, isError, error, refetch } = useAttendanceMonitoringPage(queryParams);
  const notify = useNotifyFacultyMissingAttendance(queryParams);

  return (
    <div className="space-y-5" data-figma-frame="159:8573">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Attendance Monitoring"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">
            {data?.page_subtitle ?? "Live view of classes today"}
          </p>
        </div>
        <Button
          type="button"
          className="h-9 shrink-0 gap-1.5 bg-[#245dd8] text-xs font-medium text-white hover:bg-[#1f4fb8]"
          disabled={notify.isPending || isLoading}
          onClick={() => notify.mutate()}
        >
          <CircleAlertIcon className="size-3.5" aria-hidden />
          {data?.notify_faculty_label ?? "Notify faculty"}
        </Button>
      </div>


      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            <CollegeAdminKpiGrid>
              {data.kpis.map((kpi, index) => (
                <CollegeAdminUserDashboardKpiCard key={kpi.key} kpi={kpi} index={index} />
              ))}
            </CollegeAdminKpiGrid>

            <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.not_marked_table_title}</h3>
              </div>
              {data.not_marked_rows.length ? (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[44rem] text-left text-[13px]">
                    <thead>
                      <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                        {data.not_marked_table_headers.map((header, index) => (
                          <th
                            key={header}
                            className={cn(
                              "pb-3 font-medium",
                              index === 0 ? "px-5" : "pr-3",
                              index === 4 && "text-right",
                            )}
                          >
                            {header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#f1f5f9]">
                      {data.not_marked_rows.map((row) => (
                        <tr key={row.row_key} className="hover:bg-[#f9fafb]">
                          <td className="px-5 py-3 font-medium text-[#111827]">{row.class_label}</td>
                          <td className="py-3 pr-3 text-[#374151]">{row.faculty_label}</td>
                          <td className="py-3 pr-3 tabular-nums text-[#374151]">{row.time_label}</td>
                          <td className="py-3 pr-3 text-[#374151]">{row.room_label}</td>
                          <td className="py-3 pr-3 text-right tabular-nums text-[#374151]">{row.delay_label}</td>
                          <td className="py-3 pr-5">
                            <ActionBadge label={row.action_label} tone={row.action_tone} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="px-5 py-10 text-center text-sm text-[#9ca3af]">
                  All classes scheduled for today are marked.
                </p>
              )}
              <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] px-5 py-3">
                <span className="text-[12px] text-[#6b7280]">{data.not_marked_table_footer_label}</span>
                <div className="flex gap-1">
                  <button
                    type="button"
                    disabled={page <= 1}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    className="rounded px-2 py-0.5 text-[12px] text-[#6b7280] hover:bg-[#f3f4f6] disabled:opacity-40"
                  >
                    Prev
                  </button>
                  <button
                    type="button"
                    onClick={() => setPage((p) => p + 1)}
                    className="rounded px-2 py-0.5 text-[12px] text-[#6b7280] hover:bg-[#f3f4f6]"
                  >
                    Next
                  </button>
                </div>
              </div>
            </section>

          </>
        ) : null}
      </QueryState>
    </div>
  );
}