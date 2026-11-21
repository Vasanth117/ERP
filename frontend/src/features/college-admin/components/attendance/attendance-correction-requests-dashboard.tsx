"use client";

import Link from "next/link";
import { useState } from "react";

import {
  CollegeAdminKpiGrid,
  CollegeAdminUserDashboardKpiCard,
} from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useAttendanceCorrectionRequestsPage } from "@/features/college-admin/hooks/use-attendance-corrections";
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

export function AttendanceCorrectionRequestsDashboard() {
  const [page, setPage] = useState(1);
  const queryParams = { page, page_size: 10 };
  const { data, isLoading, isError, error, refetch } = useAttendanceCorrectionRequestsPage(queryParams);

  return (
    <div className="space-y-5" data-figma-frame="159:9222">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Attendance Correction Requests"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">{data?.page_subtitle ?? "—"}</p>
        </div>
        <p className="text-[12px] tabular-nums text-[#6b7280]">{data?.updated_at_label ?? "—"}</p>
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
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.requests_table_title}</h3>
              </div>
              {data.request_rows.length ? (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[48rem] text-left text-[13px]">
                    <thead>
                      <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                        {data.requests_table_headers.map((header, index) => (
                          <th
                            key={header}
                            className={cn(
                              "px-5 py-3 font-medium",
                              index === data.requests_table_headers.length - 1 ? "text-right" : "",
                            )}
                          >
                            {header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#f1f5f9]">
                      {data.request_rows.map((row) => (
                        <tr key={row.row_key} className="text-[#111827]">
                          <td className="px-5 py-3.5 font-medium tabular-nums">{row.request_code}</td>
                          <td className="px-5 py-3.5">{row.faculty_label}</td>
                          <td className="px-5 py-3.5">{row.class_label}</td>
                          <td className="px-5 py-3.5 text-[#6b7280]">{row.session_date_label}</td>
                          <td className="px-5 py-3.5 text-[#6b7280]">{row.change_summary}</td>
                          <td className="px-5 py-3.5">
                            <StatusPill label={row.status_label} tone={row.status_tone} />
                          </td>
                          <td className="px-5 py-3.5 text-right">
                            <Link
                              href={row.review_href}
                              className="text-[12px] font-medium text-[#245dd8] hover:underline"
                            >
                              {row.review_label}
                            </Link>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="px-5 py-8 text-center text-[13px] text-[#6b7280]">No correction requests in queue.</p>
              )}
              <div className="flex items-center justify-between border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
                <span>{data.requests_table_footer_label}</span>
                <div className="flex gap-2">
                  <button
                    type="button"
                    disabled={page <= 1}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    className="rounded px-2 py-0.5 hover:bg-[#f3f4f6] disabled:opacity-40"
                  >
                    Prev
                  </button>
                  <button
                    type="button"
                    onClick={() => setPage((p) => p + 1)}
                    className="rounded px-2 py-0.5 hover:bg-[#f3f4f6]"
                  >
                    Next
                  </button>
                </div>
              </div>
            </section>

            <footer className="flex flex-wrap justify-between gap-2 border-t border-[#e8ecf2] pt-4 text-[11px] text-[#9ca3af]">
              <span>{data.footer_disclaimer}</span>
              <span>{data.footer_snapshot_label}</span>
            </footer>
          </>
        ) : null}
      </QueryState>
    </div>
  );
}