"use client";

import Link from "next/link";
import { useCallback, useMemo, useState, type ReactNode } from "react";

import { CalendarIcon } from "@/components/icons/erp/generated/calendar";
import { FilterIcon } from "@/components/icons/erp/generated/filter";
import { Button } from "@/components/ui/button";
import {
  CollegeAdminChevronDown,
  CollegeAdminChevronRight,
  CollegeAdminDownload,
} from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { CollegeAdminDashboardKpiCard, CollegeAdminKpiGrid } from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useRecentActivitiesOverview } from "@/features/college-admin/hooks/use-recent-activities-overview";
import type { DashboardDateRange } from "@/features/college-admin/types/dashboard";
import { cn } from "@/lib/utils";

const RANGE_OPTIONS: { value: DashboardDateRange | ""; label: string }[] = [
  { value: "today", label: "Today" },
  { value: "week", label: "This week" },
  { value: "month", label: "Last 30 days" },
  { value: "semester", label: "This semester" },
];


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

function ResultPill({ resultKey, label }: { resultKey: string; label: string }) {
  const tone =
    resultKey === "completed"
      ? "bg-[#ecfdf5] text-[#047857]"
      : resultKey === "errors"
        ? "bg-[#fef2f2] text-[#b91c1c]"
        : resultKey === "pending"
          ? "bg-[#eff6ff] text-[#1d4ed8]"
          : "bg-[#fff7ed] text-[#c2410c]";
  return <span className={cn("inline-flex rounded-full px-2.5 py-0.5 text-[11px] font-medium", tone)}>{label}</span>;
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

function followUpHref(item: { resource_type: string | null; resource_id: string | null }): string {
  if (item.resource_type === "import" && item.resource_id) {
    return `/college-admin/data-import/import-jobs?job=${encodeURIComponent(item.resource_id)}`;
  }
  return "/college-admin/security/administrative-audit-logs";
}

export function RecentActivitiesDashboard() {
  const [dateRange, setDateRange] = useState<DashboardDateRange>("today");
  const [moduleKey, setModuleKey] = useState("");
  const [userId, setUserId] = useState("");
  const [feedLimit, setFeedLimit] = useState(9);

  const queryParams = useMemo(
    () => ({
      range: dateRange,
      feed_limit: feedLimit,
      ...(moduleKey ? { module_key: moduleKey } : {}),
      ...(userId ? { user_id: userId } : {}),
    }),
    [dateRange, moduleKey, userId, feedLimit],
  );

  const { data, isLoading, isError, error, refetch, isFetching } = useRecentActivitiesOverview(queryParams);

  const handleExport = useCallback(() => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `recent-activities-${new Date(data.generated_at).toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data]);

  const kpis = data?.kpis;
  const moduleMax = data?.activity_by_module_max ?? 1;

  const actionsHint = useMemo(() => {
    if (kpis?.actions_vs_daily_avg_pct == null) return undefined;
    const sign = kpis.actions_vs_daily_avg_pct > 0 ? "+" : "";
    return `${sign}${kpis.actions_vs_daily_avg_pct}% vs daily average`;
  }, [kpis?.actions_vs_daily_avg_pct]);

  const activeHint = useMemo(() => {
    if (!kpis) return undefined;
    return `Across ${kpis.active_role_count} role${kpis.active_role_count === 1 ? "" : "s"}`;
  }, [kpis]);

  const canLoadMore = data ? data.feed_rows.length < data.feed_total : false;

  return (
    <div className="space-y-5" data-figma-frame="67:4394">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold text-[#111827]">Recent institutional activities</h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">A chronological feed of administrative actions across the college</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button type="button" variant="outline" className="h-9 gap-1.5 text-xs" onClick={handleExport} disabled={!data}>
            <CollegeAdminDownload className="size-3.5" />
            Export log
          </Button>
          <Link
            href="/college-admin/security/administrative-audit-logs"
            className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-3 text-xs font-medium text-white hover:bg-[#1d4ed8]"
          >
            Open audit logs
            <CollegeAdminChevronRight className="size-3.5" />
          </Link>
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <FilterSelect
            value={dateRange}
            onChange={(v) => {
              setDateRange(v as DashboardDateRange);
              setFeedLimit(9);
            }}
            active
            aria-label="Date range"
            leadingIcon={<CalendarIcon className="size-3.5" />}
            className="min-w-[8.5rem]"
          >
            {RANGE_OPTIONS.map((o) => (
              <option key={o.value || "today"} value={o.value}>
                {o.label}
              </option>
            ))}
          </FilterSelect>
          <FilterSelect
            value={moduleKey}
            onChange={(v) => {
              setModuleKey(v);
              setFeedLimit(9);
            }}
            active={!!moduleKey}
            aria-label="Module"
            leadingIcon={<FilterIcon className="size-3.5" />}
          >
            <option value="">All modules</option>
            {(data?.module_filter_options ?? []).map((m) => (
              <option key={m.module_key} value={m.module_key}>
                {m.module_label}
              </option>
            ))}
          </FilterSelect>
          <FilterSelect
            value={userId}
            onChange={(v) => {
              setUserId(v);
              setFeedLimit(9);
            }}
            active={!!userId}
            aria-label="User"
            className="min-w-[9.5rem]"
          >
            <option value="">All users</option>
            {(data?.user_filter_options ?? []).map((u) => (
              <option key={u.user_id} value={u.user_id}>
                {u.label}
              </option>
            ))}
          </FilterSelect>
        </div>
      </div>

      <QueryState isLoading={isLoading || isFetching} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            <CollegeAdminKpiGrid>
              <CollegeAdminDashboardKpiCard
                label={kpis?.actions_kpi_label ?? "Actions today"}
                value={(kpis?.actions_count ?? 0).toLocaleString("en-IN")}
                hint={actionsHint}
                hintTone={kpis?.actions_vs_daily_avg_pct && kpis.actions_vs_daily_avg_pct > 0 ? "success" : "muted"}
              />
              <CollegeAdminDashboardKpiCard
                label="Active administrators"
                value={kpis?.active_administrators ?? 0}
                hint={activeHint}
              />
              <CollegeAdminDashboardKpiCard
                label="Records changed"
                value={(kpis?.records_changed ?? 0).toLocaleString("en-IN")}
                hint={kpis?.records_changed_hint}
              />
              <CollegeAdminDashboardKpiCard
                label="Failed actions"
                value={kpis?.failed_actions ?? 0}
                hint={kpis?.failed_actions_hint}
                hintTone={kpis?.failed_actions ? "danger" : "muted"}
              />
            </CollegeAdminKpiGrid>

            <div className="grid gap-4 xl:grid-cols-3">
              <div className="xl:col-span-2">
                <Panel
                  title="Activity feed"
                  actionHref="/college-admin/security/administrative-audit-logs"
                  actionLabel="Administrative audit logs →"
                >
                  {data.feed_rows.length ? (
                    <>
                      <div className="overflow-x-auto">
                        <table className="w-full min-w-[40rem] text-left text-[12px]">
                          <thead>
                            <tr className="border-b border-[#e8ecf2] text-[#6b7280]">
                              <th className="pb-2 pr-2 font-medium">Activity</th>
                              <th className="pb-2 px-2 font-medium">Module</th>
                              <th className="pb-2 px-2 font-medium">Performed by</th>
                              <th className="pb-2 px-2 font-medium">Time</th>
                              <th className="pb-2 pl-2 font-medium">Result</th>
                            </tr>
                          </thead>
                          <tbody>
                            {data.feed_rows.map((row) => (
                              <tr key={row.activity_id} className="border-b border-[#f3f4f6] last:border-0">
                                <td className="py-3 pr-2 font-medium text-[#111827]">{row.title}</td>
                                <td className="px-2 py-3 text-[#374151]">{row.module_label}</td>
                                <td className="px-2 py-3 text-[#374151]">{row.performed_by_label}</td>
                                <td className="px-2 py-3 tabular-nums text-[#6b7280]">{row.time_label}</td>
                                <td className="py-3 pl-2">
                                  <ResultPill resultKey={row.result_key} label={row.result_label} />
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                      <div className="mt-3 flex items-center justify-between text-[11px] text-[#9ca3af]">
                        <span>
                          Showing {data.feed_rows.length} of {data.feed_total} events {kpis?.actions_period_label ?? "today"}
                        </span>
                        {canLoadMore ? (
                          <button
                            type="button"
                            className="font-medium text-[#245dd8] hover:underline"
                            onClick={() => setFeedLimit((l) => l + 9)}
                          >
                            Load more →
                          </button>
                        ) : null}
                      </div>
                    </>
                  ) : (
                    <p className="text-sm text-[#9ca3af]">No activities recorded for the current filters.</p>
                  )}
                </Panel>
              </div>

              <div className="space-y-4">
                <Panel title="Activity by module">
                  {data.activity_by_module.length ? (
                    <ul className="space-y-3">
                      {data.activity_by_module.map((item) => (
                        <li key={item.module_key}>
                          <div className="mb-1 flex justify-between text-[12px]">
                            <span className="text-[#374151]">{item.module_label}</span>
                            <span className="tabular-nums text-[#6b7280]">{item.count}</span>
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
                    <p className="text-sm text-[#9ca3af]">No module activity in range.</p>
                  )}
                </Panel>

                <Panel
                  title="Most active today"
                  actionHref="/college-admin/security/permission-access-review"
                  actionLabel="Users & permissions →"
                >
                  {data.top_performers.length ? (
                    <ul className="space-y-3">
                      {data.top_performers.map((item) => (
                        <li key={item.performer_key} className="flex items-start justify-between gap-2 text-[12px]">
                          <div>
                            <p className="font-medium text-[#111827]">{item.performer_label}</p>
                            <p className="text-[#9ca3af]">
                              {item.module_label} · {item.action_count} action{item.action_count === 1 ? "" : "s"}
                            </p>
                          </div>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm text-[#9ca3af]">No administrator activity in range.</p>
                  )}
                </Panel>

                <Panel title="Needs follow-up">
                  {data.follow_ups.length ? (
                    <ul className="space-y-3">
                      {data.follow_ups.map((item) => (
                        <li key={item.item_key} className="border-b border-[#f3f4f6] pb-3 last:border-0 last:pb-0">
                          <div className="flex items-start justify-between gap-2">
                            <div>
                              <p className="text-[12px] font-medium text-[#111827]">{item.title}</p>
                              {item.detail ? <p className="mt-0.5 text-[11px] text-[#9ca3af]">{item.detail}</p> : null}
                            </div>
                            <Link
                              href={followUpHref(item)}
                              className={cn(
                                "shrink-0 rounded-md px-2 py-1 text-[11px] font-semibold",
                                item.action_key === "fix"
                                  ? "bg-[#fef2f2] text-[#b91c1c] hover:bg-[#fee2e2]"
                                  : "bg-[#fff7ed] text-[#c2410c]",
                              )}
                            >
                              {item.action_label}
                            </Link>
                          </div>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm text-[#9ca3af]">Nothing needs follow-up right now.</p>
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