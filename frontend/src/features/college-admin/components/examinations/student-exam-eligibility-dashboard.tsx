"use client";

import { useState } from "react";
import { toast } from "sonner";

import { RefreshCwIcon } from "@/components/icons/erp/generated/refresh-cw";
import { Button } from "@/components/ui/button";
import { ExaminationRegistrationSubNav } from "@/features/college-admin/components/examinations/examination-registration-sub-nav";
import {
  CollegeAdminKpiGrid,
  CollegeAdminUserDashboardKpiCard,
} from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useRerunStudentExamEligibility, useStudentExamEligibilityPage } from "@/features/college-admin/hooks/use-student-exam-eligibility";
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
    <span className={cn("inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-medium", styles[key])}>
      <span className={cn("size-1.5 rounded-full", dot[key])} />
      {label}
    </span>
  );
}


export function StudentExamEligibilityDashboard() {
  const [page, setPage] = useState(1);
  const { data, isLoading, isError, error, refetch } = useStudentExamEligibilityPage({ page });
  const rerun = useRerunStudentExamEligibility();

  const handleRerun = () => {
    if (!data?.selected_session_id) return;
    rerun.mutate(
      { session_id: data.selected_session_id, page },
      {
        onSuccess: () => toast.success("Eligibility check completed."),
        onError: (e: Error) => toast.error(e.message),
      },
    );
  };

  return (
    <div className="space-y-5" data-figma-frame="159:12451">
      <motionHeader data={data} onRerun={handleRerun} rerunPending={rerun.isPending} />

      {data?.sub_nav?.length ? <ExaminationRegistrationSubNav items={data.sub_nav} /> : null}

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            <CollegeAdminKpiGrid>
              {data.kpis.map((kpi, index) => (
                <CollegeAdminUserDashboardKpiCard key={kpi.key} kpi={kpi} index={index} />
              ))}
            </CollegeAdminKpiGrid>

            <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="flex items-center justify-between border-b border-[#f1f5f9] px-5 py-3.5">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.ineligible_section_title}</h3>
                <span className="text-[12px] text-[#6b7280]">{data.ineligible_count_label}</span>
              </div>
              {data.ineligible_rows.length ? (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[48rem] text-left text-[13px]">
                    <thead>
                      <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                        {data.table_headers.map((header, index) => (
                          <th key={header} className={cn("pb-3 font-medium", index === 0 ? "pl-5 pr-3" : "pr-3", index === data.table_headers.length - 1 ? "pr-5" : "")}>
                            {header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#f1f5f9]">
                      {data.ineligible_rows.map((row) => (
                        <tr key={`${row.register_number}-${row.student_name}`}>
                          <td className="pl-5 py-3 pr-3 font-medium text-[#111827]">{row.student_name}</td>
                          <td className="py-3 pr-3 font-mono text-[12px] text-[#6b7280]">{row.register_number}</td>
                          <td className="py-3 pr-3">{row.reason_label}</td>
                          <td className="py-3 pr-3 tabular-nums">{row.attendance_label}</td>
                          <td className="py-3 pr-3">
                            <StatusPill label={row.fee_status_label} tone={row.fee_status_tone} />
                          </td>
                          <td className="py-3 pr-5">
                            <StatusPill label={row.decision_label} tone={row.decision_tone} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="px-5 py-10 text-center text-sm text-[#9ca3af]">No ineligible students in this session.</p>
              )}
              <motionPagination data={data} page={page} setPage={setPage} />
            </section>

          </>
        ) : null}
      </QueryState>
    </div>
  );
}

function motionHeader({
  data,
  onRerun,
  rerunPending,
}: {
  data?: { page_title?: string; page_subtitle?: string; rerun_check_label?: string };
  onRerun: () => void;
  rerunPending: boolean;
}) {
  return (
    <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
      <div>
        <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">{data?.page_title ?? "Student Exam Eligibility"}</h2>
        <p className="mt-1 text-[14px] text-[#6b7280]">{data?.page_subtitle ?? "—"}</p>
      </div>
      <div className="flex flex-col items-end gap-2">
        <Button type="button" className="h-9 gap-1.5 bg-[#245dd8] text-xs font-medium hover:bg-[#1f4fb8]" disabled={rerunPending} onClick={onRerun}>
          <RefreshCwIcon className="size-3.5" aria-hidden />
          {data?.rerun_check_label ?? "Re-run check"}
        </Button>
      </div>
    </div>
  );
}

function motionPagination({
  data,
  page,
  setPage,
}: {
  data: { showing_label: string; pagination: { total_pages: number; page: number; page_numbers: number[]; has_previous: boolean; has_next: boolean } };
  page: number;
  setPage: (p: number) => void;
}) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
      <span>{data.showing_label}</span>
      {data.pagination.total_pages > 0 ? (
        <div className="flex items-center gap-1">
          <button type="button" className="rounded border border-[#dce3ec] px-2 py-1 disabled:opacity-40" disabled={!data.pagination.has_previous} onClick={() => setPage(Math.max(1, page - 1))}>
            ‹
          </button>
          {data.pagination.page_numbers.map((num, index) =>
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
                  num === data.pagination.page ? "border-[#245dd8] bg-[#eff6ff] text-[#245dd8]" : "border-[#dce3ec]",
                )}
                onClick={() => setPage(num)}
              >
                {num}
              </button>
            ),
          )}
          <button type="button" className="rounded border border-[#dce3ec] px-2 py-1 disabled:opacity-40" disabled={!data.pagination.has_next} onClick={() => setPage(page + 1)}>
            ›
          </button>
        </div>
      ) : null}
    </div>
  );
}