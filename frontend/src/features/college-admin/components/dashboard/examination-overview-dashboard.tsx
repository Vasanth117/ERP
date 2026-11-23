"use client";

import Link from "next/link";
import { CollegeAdminDashboardPanel as Panel } from "@/features/college-admin/components/ui/dashboard-panel-ui";
import { useMemo, type ReactNode } from "react";

import { CalendarIcon } from "@/components/icons/erp/generated/calendar";
import { MailWarningIcon } from "@/components/icons/erp/generated/mail-warning";
import {
  CollegeAdminChevronRight,
} from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { CollegeAdminDashboardKpiCard, CollegeAdminKpiGrid } from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useExaminationOverview } from "@/features/college-admin/hooks/use-examination-overview";
import { cn } from "@/lib/utils";

function formatSubmitted(iso: string | null | undefined) {
  if (!iso) return "";
  try {
    return new Intl.DateTimeFormat("en-IN", { day: "numeric", month: "short" }).format(new Date(iso));
  } catch {
    return "";
  }
}

function StatusPill({ statusKey, label }: { statusKey: string; label: string }) {
  const tone =
    statusKey === "ready" || statusKey === "done"
      ? "bg-[#ecfdf5] text-[#047857]"
      : statusKey === "invigilators_due" || statusKey === "seating_pending" || statusKey === "pending" || statusKey === "in_progress"
        ? "bg-[#fff7ed] text-[#c2410c]"
        : "bg-[#f1f5f9] text-[#64748b]";
  const dot =
    statusKey === "ready" || statusKey === "done"
      ? "bg-[#10b981]"
      : statusKey === "at_risk"
        ? "bg-[#ef4444]"
        : statusKey === "not_started"
          ? "bg-[#94a3b8]"
          : "bg-[#f97316]";
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-medium", tone)}>
      <span className={cn("size-1.5 rounded-full", dot)} />
      {label}
    </span>
  );
}


function ResultBars({ items }: { items: { label: string; rate: number | null }[] }) {
  if (!items.length) {
    return <p className="text-sm text-[#9ca3af]">No published result data for this examination cycle yet.</p>;
  }
  const max = Math.max(...items.map((i) => i.rate ?? 0), 1);
  return (
    <div className="flex h-44 items-end justify-between gap-2">
      {items.map((item) => (
        <div key={item.label} className="flex flex-1 flex-col items-center gap-1">
          <span className="text-[10px] tabular-nums text-[#6b7280]">{item.rate != null ? `${item.rate}%` : "—"}</span>
          <div
            className="w-full max-w-[52px] rounded-t-md bg-[#245dd8]"
            style={{ height: `${item.rate != null ? Math.max(8, (item.rate / max) * 100) : 4}%` }}
          />
          <span className="max-w-[3.5rem] text-center text-[9px] leading-tight text-[#9ca3af]">{item.label}</span>
        </div>
      ))}
    </div>
  );
}

function ReadinessIcon({ statusKey }: { statusKey: string }) {
  const cls =
    statusKey === "done"
      ? "border-[#10b981] bg-[#ecfdf5] text-[#047857]"
      : statusKey === "pending" || statusKey === "in_progress"
        ? "border-[#f97316] bg-[#fff7ed] text-[#c2410c]"
        : "border-[#e2e8f0] bg-[#f8fafc] text-[#94a3b8]";
  return (
    <span className={cn("flex size-7 shrink-0 items-center justify-center rounded-full border text-[11px] font-bold", cls)}>
      {statusKey === "done" ? "✓" : statusKey === "not_started" ? "○" : "!"}
    </span>
  );
}

export function ExaminationOverviewDashboard() {
  const { data, isLoading, isError, error, refetch, isFetching } = useExaminationOverview();

  const kpis = data?.kpis;
  const upcoming = kpis?.upcoming_session;
  const resultBars = useMemo(
    () =>
      (data?.result_summary_bars ?? []).map((b) => ({
        label: b.label,
        rate: b.pass_rate_pct,
      })),
    [data?.result_summary_bars],
  );

  const pendingHint = useMemo(() => {
    const items = kpis?.results_pending ?? [];
    if (!items.length) return "No sessions awaiting publication";
    if (items.length === 1) return items[0].label;
    return `${items[0].label} +${items.length - 1} more`;
  }, [kpis?.results_pending]);

  const hallHint = useMemo(() => {
    const pct = kpis?.hall_tickets_issued_pct;
    const withheld = kpis?.hall_tickets_withheld ?? 0;
    if (pct == null && withheld === 0) return "No hall tickets issued yet";
    return `${pct ?? 0}% · ${withheld} withheld for dues`;
  }, [kpis]);

  const upcomingHint = useMemo(() => {
    if (!upcoming?.date_range_label) return "No examination session scheduled";
    const days = upcoming.days_to_go;
    const daysText = days != null ? ` · ${days} day${days === 1 ? "" : "s"} to go` : "";
    return `${upcoming.date_range_label}${daysText}`;
  }, [upcoming]);

  return (
    <div className="space-y-5" data-figma-frame="66:2970">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold text-[#111827]">Examination overview</h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">
            Readiness, schedule and results for the current examination cycle
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link
            href="/college-admin/examination-administration"
            className="inline-flex h-9 items-center gap-1.5 rounded-md border border-[#e5e7eb] bg-white px-3 text-xs font-medium text-[#374151] hover:bg-[#f9fafb]"
          >
            <CalendarIcon className="size-3.5" />
            View timetable
          </Link>
          <Link
            href="/college-admin/examination-administration/sessions"
            className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-3 text-xs font-medium text-white hover:bg-[#1d4ed8]"
          >
            Open examination centre
            <CollegeAdminChevronRight className="size-3.5" />
          </Link>
        </div>
      </div>

      <QueryState isLoading={isLoading || isFetching} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            {data.timetable_alert ? <TimetableAlertBanner alert={data.timetable_alert} /> : null}

            <CollegeAdminKpiGrid>
              <CollegeAdminDashboardKpiCard
                label="Upcoming session"
                value={upcoming?.session_name ?? "—"}
                hint={upcomingHint}
              />
              <CollegeAdminDashboardKpiCard
                label="Papers scheduled"
                value={kpis?.papers_scheduled ?? 0}
                hint={`Across ${kpis?.programmes_count ?? 0} programmes`}
              />
              <CollegeAdminDashboardKpiCard
                label="Hall tickets issued"
                value={(kpis?.hall_tickets_issued ?? 0).toLocaleString("en-IN")}
                hint={hallHint}
              />
              <CollegeAdminDashboardKpiCard
                label="Results pending"
                value={kpis?.results_pending_count ?? 0}
                hint={pendingHint}
                hintTone="info"
              />
            </CollegeAdminKpiGrid>

            <div className="grid gap-4 xl:grid-cols-3">
              <div className="space-y-4 xl:col-span-2">
                <Panel
                  title="Upcoming examination schedule"
                  actionHref="/college-admin/examination-administration"
                  actionLabel="View all sessions →"
                >
                  {data.upcoming_schedule.length ? (
                    <>
                      <div className="overflow-x-auto">
                        <table className="w-full min-w-[42rem] text-left text-[12px]">
                          <thead>
                            <tr className="border-b border-[#e8ecf2] text-[#6b7280]">
                              <th className="pb-2 pr-2 font-medium">Date & session</th>
                              <th className="pb-2 px-2 font-medium">Programme</th>
                              <th className="pb-2 px-2 text-right font-medium">Papers</th>
                              <th className="pb-2 px-2 text-right font-medium">Candidates</th>
                              <th className="pb-2 px-2 text-right font-medium">Halls</th>
                              <th className="pb-2 pl-2 font-medium">Status</th>
                            </tr>
                          </thead>
                          <tbody>
                            {data.upcoming_schedule.map((row) => (
                              <tr key={row.row_key} className="border-b border-[#f1f5f9]">
                                <td className="py-2 pr-2 font-medium text-[#111827]">{row.date_session_label}</td>
                                <td className="px-2 py-2">{row.programme_label}</td>
                                <td className="px-2 py-2 text-right tabular-nums">{row.papers_count}</td>
                                <td className="px-2 py-2 text-right tabular-nums">
                                  {row.candidates_count ?? "—"}
                                </td>
                                <td className="px-2 py-2 text-right tabular-nums">{row.halls_count ?? "—"}</td>
                                <td className="py-2 pl-2">
                                  <StatusPill statusKey={row.status_key} label={row.status_label} />
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                      <p className="mt-3 border-t border-[#f1f5f9] pt-3 text-[11px] text-[#6b7280]">
                        Showing {data.upcoming_schedule.length} of {data.upcoming_schedule_total} sessions
                      </p>
                    </>
                  ) : (
                    <p className="text-sm text-[#9ca3af]">No upcoming timetable slots for the focused session.</p>
                  )}
                </Panel>

                <Panel
                  title={data.result_summary_title ? `Result summary – ${data.result_summary_title}` : "Result summary"}
                  actionHref="/college-admin/examination-administration"
                  actionLabel="Result processing →"
                >
                  <ResultBars items={resultBars} />
                </Panel>
              </div>

              <div className="space-y-4">
                <Panel
                  title="Readiness checklist"
                  actionHref="/college-admin/examination-administration"
                  actionLabel="Exam configuration →"
                >
                  <ul className="space-y-4">
                    {data.readiness_checklist.map((step) => (
                      <li key={step.step_key} className="flex gap-3">
                        <ReadinessIcon statusKey={step.status_key} />
                        <div className="min-w-0 flex-1">
                          <div className="flex items-start justify-between gap-2">
                            <p className="text-[13px] font-semibold text-[#111827]">{step.label}</p>
                            <StatusPill statusKey={step.status_key} label={step.status_label} />
                          </div>
                          <p className="mt-0.5 text-[11px] text-[#9ca3af]">{step.description}</p>
                        </div>
                      </li>
                    ))}
                  </ul>
                </Panel>

                <Panel
                  title="Post-result activity"
                  actionHref="/college-admin/examination-administration"
                  actionLabel="Revaluation →"
                >
                  <ul className="divide-y divide-[#f1f5f9]">
                    {data.post_result_activity.map((item) => (
                      <li key={item.item_key} className="flex items-center justify-between gap-2 py-3 first:pt-0">
                        <div>
                          <p className="text-[13px] font-semibold text-[#111827]">{item.label}</p>
                          {item.description ? <p className="text-[11px] text-[#9ca3af]">{item.description}</p> : null}
                        </div>
                        <span className="rounded-full bg-[#eff6ff] px-2.5 py-0.5 text-[12px] font-semibold tabular-nums text-[#1d4ed8]">
                          {item.count}
                        </span>
                      </li>
                    ))}
                  </ul>
                </Panel>
              </div>
            </div>

          </>
        ) : null}
      </QueryState>
    </div>
  );
}

function TimetableAlertBanner({
  alert,
}: {
  alert: import("@/features/college-admin/types/examination-overview").ExaminationTimetableAlert;
}) {
  const submitted = formatSubmitted(alert.submitted_at);
  return (
    <div className="flex flex-col gap-2 rounded-xl border border-[#fde68a] bg-[#fffbeb] p-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex gap-3">
        <MailWarningIcon className="mt-0.5 size-5 shrink-0 text-[#d97706]" aria-hidden />
        <div>
          <p className="text-[13px] font-semibold text-[#92400e]">{alert.title}</p>
          <p className="mt-1 text-[12px] text-[#a16207]">
            {alert.description}
            {submitted ? ` · Submitted ${submitted}` : ""}
          </p>
        </div>
      </div>
      <Link
        href="/college-admin/examination-administration"
        className="shrink-0 text-[12px] font-medium text-[#245dd8] hover:underline"
      >
        {alert.review_href_note ?? "Review timetable"} →
      </Link>
    </div>
  );
}