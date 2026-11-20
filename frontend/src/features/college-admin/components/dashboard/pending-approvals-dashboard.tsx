"use client";

import Link from "next/link";
import { useMemo, useState, type ReactNode } from "react";

import { CalendarIcon } from "@/components/icons/erp/generated/calendar";
import { FilterIcon } from "@/components/icons/erp/generated/filter";
import { Settings2Icon } from "@/components/icons/erp/generated/settings-2";
import { SquareCheckIcon } from "@/components/icons/erp/generated/square-check";
import {
  CollegeAdminChevronDown,
  CollegeAdminChevronRight,
} from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { usePendingApprovalsOverview } from "@/features/college-admin/hooks/use-pending-approvals-overview";
import type { DashboardDateRange } from "@/features/college-admin/types/dashboard";
import type { PendingApprovalQueueRow } from "@/features/college-admin/types/pending-approvals-overview";
import { cn } from "@/lib/utils";

const RANGE_OPTIONS: { value: DashboardDateRange | ""; label: string }[] = [
  { value: "", label: "All dates" },
  { value: "today", label: "Today" },
  { value: "week", label: "This week" },
  { value: "month", label: "Last 30 days" },
  { value: "semester", label: "This semester" },
];


function formatDecidedAt(iso: string) {
  try {
    const dt = new Date(iso);
    const now = new Date();
    const sameDay =
      dt.getDate() === now.getDate() &&
      dt.getMonth() === now.getMonth() &&
      dt.getFullYear() === now.getFullYear();
    const time = new Intl.DateTimeFormat("en-IN", {
      hour: "2-digit",
      minute: "2-digit",
      timeZone: "Asia/Kolkata",
    }).format(dt);
    return sameDay ? `today ${time}` : new Intl.DateTimeFormat("en-IN", { day: "numeric", month: "short" }).format(dt);
  } catch {
    return "—";
  }
}

function reviewHref(row: PendingApprovalQueueRow): string {
  const params = new URLSearchParams({
    id: row.review_resource_id,
    type: row.review_resource_type,
  });
  return `/college-admin/approvals/approval-request-details?${params.toString()}`;
}

function Panel({
  title,
  children,
  actionHref,
  actionLabel,
}: {
  title: string;
  children: ReactNode;
  actionHref?: string;
  actionLabel?: string;
}) {
  return (
    <section className="rounded-xl border border-[#e8ecf2] bg-white p-4 shadow-[0_1px_2px_rgba(15,23,42,0.04)] sm:p-5">
      <div className="mb-4 flex items-center justify-between gap-2">
        <h3 className="text-[14px] font-semibold text-[#111827]">{title}</h3>
        {actionHref && actionLabel ? (
          <Link href={actionHref} className="text-[12px] font-medium text-[#245dd8] hover:underline">
            {actionLabel}
          </Link>
        ) : null}
      </div>
      {children}
    </section>
  );
}

function KpiCard({
  label,
  value,
  hint,
  hintTone,
}: {
  label: string;
  value: string | number;
  hint?: ReactNode;
  hintTone?: "danger" | "success" | "warning" | "muted";
}) {
  const toneClass =
    hintTone === "danger"
      ? "text-[#dc2626]"
      : hintTone === "success"
        ? "text-[#047857]"
        : hintTone === "warning"
          ? "text-[#d97706]"
          : "text-[#9ca3af]";
  return (
    <div className="flex min-h-[7.25rem] flex-col rounded-xl border border-[#e8ecf2] bg-white p-5">
      <p className="text-[12px] font-medium text-[#6b7280]">{label}</p>
      <p
        className={cn(
          "mt-3 text-[1.75rem] font-bold tabular-nums",
          hintTone === "danger" ? "text-[#dc2626]" : "text-[#111827]",
        )}
      >
        {value}
      </p>
      {hint ? <p className={cn("mt-auto pt-3 text-[12px]", toneClass)}>{hint}</p> : <span className="mt-auto block min-h-[1.125rem]" aria-hidden />}
    </div>
  );
}

function SlaPill({ slaKey, label }: { slaKey: string; label: string }) {
  const tone =
    slaKey === "overdue"
      ? "bg-[#fef2f2] text-[#b91c1c]"
      : slaKey === "due_today"
        ? "bg-[#fff7ed] text-[#c2410c]"
        : "bg-[#eff6ff] text-[#1d4ed8]";
  return <span className={cn("inline-flex rounded-full px-2.5 py-0.5 text-[11px] font-medium", tone)}>{label}</span>;
}

function PriorityPill({ priorityKey, label }: { priorityKey: string; label: string }) {
  const dot = priorityKey === "high" ? "bg-[#ef4444]" : "bg-[#f97316]";
  return (
    <span className="inline-flex items-center gap-1.5 text-[11px] font-medium text-[#374151]">
      <span className={cn("size-1.5 rounded-full", dot)} />
      {label}
    </span>
  );
}

function FilterSelect({
  value,
  onChange,
  active,
  children,
  disabled,
  "aria-label": ariaLabel,
  className,
  leadingIcon,
}: {
  value: string;
  onChange: (v: string) => void;
  active?: boolean;
  children: ReactNode;
  disabled?: boolean;
  "aria-label"?: string;
  className?: string;
  leadingIcon?: ReactNode;
}) {
  return (
    <div className={cn("relative inline-flex min-w-[8.75rem]", className)}>
      {leadingIcon ? (
        <span
          className={cn(
            "pointer-events-none absolute left-2.5 top-1/2 z-[1] -translate-y-1/2",
            active ? "text-[#245dd8]" : "text-[#6b7280]",
          )}
          aria-hidden
        >
          {leadingIcon}
        </span>
      ) : null}
      <select
        aria-label={ariaLabel}
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
        className={cn(
          "w-full appearance-none truncate rounded-md border py-1.5 pr-8 text-xs",
          leadingIcon ? "pl-8" : "pl-3",
          active ? "border-[#245dd8] bg-[#eef4ff] font-medium text-[#245dd8]" : "border-[#e5e7eb] bg-white text-[#374151]",
          disabled && "opacity-60",
        )}
      >
        {children}
      </select>
      <CollegeAdminChevronDown className="pointer-events-none absolute right-2 top-1/2 size-3.5 -translate-y-1/2 text-[#6b7280]" />
    </div>
  );
}

export function PendingApprovalsDashboard() {
  const [dateRange, setDateRange] = useState<DashboardDateRange | "">("");
  const [moduleKey, setModuleKey] = useState("");
  const [requesterId, setRequesterId] = useState("");

  const queryParams = useMemo(
    () => ({
      ...(dateRange ? { range: dateRange as DashboardDateRange } : {}),
      ...(moduleKey ? { module_key: moduleKey } : {}),
      ...(requesterId ? { requester_id: requesterId } : {}),
    }),
    [dateRange, moduleKey, requesterId],
  );

  const { data, isLoading, isError, error, refetch, isFetching } = usePendingApprovalsOverview(queryParams);

  const kpis = data?.kpis;

  const awaitingHint = useMemo(() => {
    if (!kpis) return undefined;
    return `Across ${kpis.modules_with_pending} module${kpis.modules_with_pending === 1 ? "" : "s"}`;
  }, [kpis]);

  const overdueHint = useMemo(() => {
    if (!kpis) return undefined;
    return `Past SLA by ${kpis.overdue_sla_days}+ days`;
  }, [kpis]);

  const approvedHint = useMemo(() => {
    if (!kpis?.avg_turnaround_days) return "No completions this week";
    return `Avg. ${kpis.avg_turnaround_days} days turnaround`;
  }, [kpis?.avg_turnaround_days]);

  const escalatedHint = useMemo(() => {
    if (!kpis?.escalated_to_college_admin) return "No escalations";
    return "From HoDs and Registrar";
  }, [kpis?.escalated_to_college_admin]);

  const moduleMax = data?.pending_by_module_max ?? 1;

  return (
    <div className="space-y-5" data-figma-frame="67:3905">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold text-[#111827]">Pending approvals</h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">Requests awaiting your decision across all modules</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link
            href="/college-admin/approvals/approval-workflow-configuration"
            className="inline-flex h-9 items-center gap-1.5 rounded-md border border-[#e5e7eb] bg-white px-3 text-xs font-medium text-[#374151] hover:bg-[#f9fafb]"
          >
            <Settings2Icon className="size-3.5" />
            Workflow settings
          </Link>
          <Link
            href="/college-admin/approvals/approval-dashboard"
            className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-3 text-xs font-medium text-white hover:bg-[#1d4ed8]"
          >
            Open approval centre
            <CollegeAdminChevronRight className="size-3.5" />
          </Link>
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <FilterSelect
            value={dateRange}
            onChange={(v) => setDateRange(v as DashboardDateRange | "")}
            active={!!dateRange}
            aria-label="Date range"
            leadingIcon={<CalendarIcon className="size-3.5" />}
            className="min-w-[9rem]"
          >
            {RANGE_OPTIONS.map((o) => (
              <option key={o.value || "all"} value={o.value}>
                {o.label}
              </option>
            ))}
          </FilterSelect>
          <FilterSelect
            value={moduleKey}
            onChange={setModuleKey}
            active={!!moduleKey}
            aria-label="Module"
            leadingIcon={<FilterIcon className="size-3.5" />}
            className="min-w-[9.5rem]"
          >
            <option value="">All modules</option>
            {(data?.module_filter_options ?? []).map((m) => (
              <option key={m.module_key} value={m.module_key}>
                {m.module_label}
              </option>
            ))}
          </FilterSelect>
          <FilterSelect
            value={requesterId}
            onChange={setRequesterId}
            active={!!requesterId}
            aria-label="Requester"
            className="min-w-[10rem]"
          >
            <option value="">All requesters</option>
            {(data?.requester_filter_options ?? []).map((r) => (
              <option key={r.user_id} value={r.user_id}>
                {r.label}
              </option>
            ))}
          </FilterSelect>
        </div>
      </div>

      <QueryState isLoading={isLoading || isFetching} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
              <KpiCard label="Awaiting your action" value={kpis?.awaiting_action ?? 0} hint={awaitingHint} />
              <KpiCard
                label="Overdue"
                value={kpis?.overdue_count ?? 0}
                hint={overdueHint}
                hintTone={kpis?.overdue_count ? "danger" : "muted"}
              />
              <KpiCard
                label="Approved this week"
                value={kpis?.approved_this_week ?? 0}
                hint={approvedHint}
                hintTone="success"
              />
              <KpiCard
                label="Escalated to you"
                value={kpis?.escalated_to_college_admin ?? 0}
                hint={escalatedHint}
                hintTone={kpis?.escalated_to_college_admin ? "warning" : "muted"}
              />
            </div>

            <div className="grid gap-4 xl:grid-cols-3">
              <div className="xl:col-span-2">
                <Panel title="Requests awaiting approval">
                  {data.queue_rows.length ? (
                    <>
                      <div className="overflow-x-auto">
                        <table className="w-full min-w-[40rem] text-left text-[12px]">
                          <thead>
                            <tr className="border-b border-[#e8ecf2] text-[#6b7280]">
                              <th className="pb-2 pr-2 font-medium">Request</th>
                              <th className="pb-2 px-2 font-medium">Module</th>
                              <th className="pb-2 px-2 font-medium">Requested by</th>
                              <th className="pb-2 px-2 font-medium">Submitted</th>
                              <th className="pb-2 px-2 font-medium">SLA</th>
                              <th className="pb-2 pl-2 text-right font-medium">Action</th>
                            </tr>
                          </thead>
                          <tbody>
                            {data.queue_rows.map((row) => (
                              <tr key={row.reference_id} className="border-b border-[#f3f4f6] last:border-0">
                                <td className="py-3 pr-2">
                                  <p className="font-mono text-[10px] text-[#9ca3af]">{row.request_code}</p>
                                  <p className="font-medium text-[#111827]">{row.title}</p>
                                </td>
                                <td className="px-2 py-3 text-[#374151]">{row.module_label}</td>
                                <td className="px-2 py-3 text-[#374151]">{row.requested_by_label}</td>
                                <td className="px-2 py-3 text-[#6b7280]">{row.submitted_label}</td>
                                <td className="px-2 py-3">
                                  <SlaPill slaKey={row.sla_key} label={row.sla_label} />
                                </td>
                                <td className="py-3 pl-2 text-right">
                                  <Link href={reviewHref(row)} className="text-[12px] font-medium text-[#245dd8] hover:underline">
                                    Review →
                                  </Link>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                      <div className="mt-3 flex items-center justify-between text-[11px] text-[#9ca3af]">
                        <span>
                          Showing {data.queue_rows.length} of {data.queue_total} · sorted by SLA
                        </span>
                        <Link href="/college-admin/approvals/pending-approval-requests" className="font-medium text-[#245dd8] hover:underline">
                          View all →
                        </Link>
                      </div>
                    </>
                  ) : (
                    <p className="text-sm text-[#9ca3af]">No pending requests match the current filters.</p>
                  )}
                </Panel>
              </div>

              <div className="space-y-4">
                <Panel
                  title="Pending by module"
                  actionHref="/college-admin/approvals/approval-dashboard"
                  actionLabel="Approval dashboard →"
                >
                  {data.pending_by_module.length ? (
                    <ul className="space-y-3">
                      {data.pending_by_module.map((item) => (
                        <li key={item.module_key}>
                          <div className="mb-1 flex items-center justify-between gap-2 text-[12px]">
                            <span className="text-[#374151]">{item.module_label}</span>
                            <span className="shrink-0 text-[#6b7280]">
                              {item.count} request{item.count === 1 ? "" : "s"}
                            </span>
                          </div>
                          <div className="h-2 rounded-full bg-[#eef2f7]">
                            <div
                              className="h-full rounded-full bg-[#245dd8]"
                              style={{ width: `${Math.max(6, (item.count / moduleMax) * 100)}%` }}
                            />
                          </div>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm text-[#9ca3af]">No module breakdown for current filters.</p>
                  )}
                </Panel>

                <Panel
                  title="Escalations"
                  actionHref="/college-admin/approvals/escalation-management"
                  actionLabel="Escalation management →"
                >
                  {data.escalations.length ? (
                    <ul className="space-y-3">
                      {data.escalations.map((item) => (
                        <li key={item.escalation_id} className="border-b border-[#f3f4f6] pb-3 last:border-0 last:pb-0">
                          <p className="text-[12px] font-medium text-[#111827]">{item.title}</p>
                          <div className="mt-1 flex flex-wrap items-center justify-between gap-2">
                            <p className="text-[11px] text-[#9ca3af]">
                              Escalated by {item.escalated_by_label} · {item.age_days} day{item.age_days === 1 ? "" : "s"}
                            </p>
                            <PriorityPill priorityKey={item.priority_key} label={item.priority_label} />
                          </div>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm text-[#9ca3af]">No escalations at this time.</p>
                  )}
                </Panel>

                <Panel
                  title="Recently decided"
                  actionHref="/college-admin/approvals/approval-history"
                  actionLabel="Approval history →"
                >
                  {data.recently_decided.length ? (
                    <ul className="space-y-3">
                      {data.recently_decided.map((item) => (
                        <li key={item.event_id} className="flex gap-2 border-b border-[#f3f4f6] pb-3 last:border-0 last:pb-0">
                          {item.decision_key === "approved" ? (
                            <SquareCheckIcon className="mt-0.5 size-4 shrink-0 text-[#10b981]" />
                          ) : (
                            <span className="mt-0.5 flex size-4 shrink-0 items-center justify-center rounded-full bg-[#fef2f2] text-[10px] font-bold text-[#dc2626]">
                              !
                            </span>
                          )}
                          <div>
                            <p className="text-[12px] font-medium text-[#111827]">{item.title}</p>
                            <p className="mt-0.5 text-[11px] text-[#9ca3af]">
                              {item.decision_label}
                              {item.detail ? ` · ${item.detail}` : ""} · {formatDecidedAt(item.decided_at)}
                            </p>
                          </div>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm text-[#9ca3af]">No recent approval decisions recorded.</p>
                  )}
                </Panel>
              </div>
            </div>

          </>
        ) : null}
      </QueryState>
    </div>
  );
}