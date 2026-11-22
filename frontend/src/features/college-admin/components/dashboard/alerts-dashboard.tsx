"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import { CollegeAdminDashboardPanel as Panel } from "@/features/college-admin/components/ui/dashboard-panel-ui";
import { CircleIcon } from "@/components/icons/erp/generated/circle";
import { Settings2Icon } from "@/components/icons/erp/generated/settings-2";
import { SlidersHorizontalIcon } from "@/components/icons/erp/generated/sliders-horizontal";
import { SquareCheckIcon } from "@/components/icons/erp/generated/square-check";
import { Button } from "@/components/ui/button";
import { CollegeAdminChevronRight } from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { CollegeAdminDashboardKpiCard, CollegeAdminKpiGrid } from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useAlertsOverview, useMarkAllAlertsRead } from "@/features/college-admin/hooks/use-alerts-overview";
import type { DashboardAlertItem } from "@/features/college-admin/types/alerts-overview";
import { cn } from "@/lib/utils";


function SeverityIcon({ severityKey }: { severityKey: string }) {
  if (severityKey === "critical") {
    return (
      <span className="flex size-7 shrink-0 items-center justify-center rounded-full bg-[#fef2f2] text-[#dc2626]" aria-hidden>
        !
      </span>
    );
  }
  if (severityKey === "warning") {
    return (
      <span className="flex size-7 shrink-0 items-center justify-center rounded-full bg-[#fff7ed] text-[#d97706]" aria-hidden>
        △
      </span>
    );
  }
  return (
    <span className="flex size-7 shrink-0 items-center justify-center rounded-full bg-[#eff6ff] text-[#1d4ed8]" aria-hidden>
      i
    </span>
  );
}

function SeverityPill({ label, severityKey }: { label: string; severityKey: string }) {
  const tone =
    severityKey === "critical"
      ? "bg-[#fef2f2] text-[#b91c1c]"
      : severityKey === "warning"
        ? "bg-[#fff7ed] text-[#c2410c]"
        : "bg-[#eff6ff] text-[#1d4ed8]";
  return <span className={cn("rounded-full px-2 py-0.5 text-[10px] font-medium", tone)}>{label}</span>;
}

function AlertRow({ row }: { row: DashboardAlertItem }) {
  return (
    <li className="flex gap-3 border-b border-[#f3f4f6] py-3 last:border-0">
      <SeverityIcon severityKey={row.severity_key} />
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <p className="text-[13px] font-medium text-[#111827]">{row.title}</p>
          <SeverityPill label={row.severity_label} severityKey={row.severity_key} />
        </div>
        {row.summary ? <p className="mt-1 text-[11px] text-[#9ca3af]">{row.summary}</p> : null}
        <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-[#6b7280]">
          <span>{row.module_label}</span>
          <span>·</span>
          <span>{row.time_label}</span>
          <Link
            href={row.action_href}
            className={cn(
              "ml-auto rounded-md px-2 py-1 text-[11px] font-semibold",
              row.severity_key === "critical"
                ? "bg-[#245dd8] text-white hover:bg-[#1d4ed8]"
                : "border border-[#e5e7eb] text-[#374151] hover:bg-[#f9fafb]",
            )}
          >
            {row.action_label}
          </Link>
        </div>
      </div>
    </li>
  );
}

export function AlertsDashboard() {
  const { data, isLoading, isError, error, refetch, isFetching } = useAlertsOverview();
  const markRead = useMarkAllAlertsRead();

  const kpis = data?.kpis;
  const moduleMax = data?.alerts_by_module_max ?? 1;

  return (
    <div className="space-y-5" data-figma-frame="67:4882">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold text-[#111827]">Alerts &amp; notifications</h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">Time-sensitive issues and system notices that need College Admin attention</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link
            href="/college-admin/communication-administration"
            className="inline-flex h-9 items-center gap-1.5 rounded-md border border-[#e5e7eb] bg-white px-3 text-xs font-medium text-[#374151] hover:bg-[#f9fafb]"
          >
            <SlidersHorizontalIcon className="size-3.5" />
            Notification settings
          </Link>
          <Button
            type="button"
            className="h-9 gap-1.5 bg-[#245dd8] text-xs text-white"
            disabled={markRead.isPending || !data?.all_alerts.length}
            onClick={() => void markRead.mutateAsync()}
          >
            <SquareCheckIcon className="size-3.5" />
            Mark all as read
          </Button>
        </div>
      </div>

      <QueryState isLoading={isLoading || isFetching} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            <CollegeAdminKpiGrid>
              <CollegeAdminDashboardKpiCard
                label="Critical"
                value={kpis?.critical_count ?? 0}
                hint={kpis?.critical_hint}
                hintTone={kpis?.critical_count ? "danger" : "muted"}
                kpiKey="critical"
                index={0}
              />
              <CollegeAdminDashboardKpiCard
                label="Warnings"
                value={kpis?.warning_count ?? 0}
                hint={kpis?.warning_hint}
                kpiKey="warnings"
                index={1}
              />
              <CollegeAdminDashboardKpiCard
                label="Information"
                value={kpis?.info_count ?? 0}
                hint={kpis?.info_hint}
                kpiKey="information"
                index={2}
              />
              <CollegeAdminDashboardKpiCard
                label="Resolved today"
                value={kpis?.resolved_today ?? 0}
                hint={kpis?.resolved_hint}
                hintTone="success"
                kpiKey="resolved_today"
                index={3}
              />
            </CollegeAdminKpiGrid>

            {data.featured ? (
              <div className="rounded-xl border border-[#fecaca] bg-[#fef2f2] p-4 sm:p-5">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <p className="text-[15px] font-semibold text-[#991b1b]">{data.featured.title}</p>
                    {data.featured.summary ? <p className="mt-1 text-[13px] text-[#b91c1c]/90">{data.featured.summary}</p> : null}
                  </div>
                  <Link href={data.featured.action_href} className="shrink-0 text-[13px] font-medium text-[#245dd8] hover:underline">
                    {data.featured.action_label}
                  </Link>
                </div>
              </div>
            ) : null}

            <div className="grid gap-4 xl:grid-cols-3">
              <div className="xl:col-span-2">
                <Panel title="All alerts" actionHref="/college-admin/security/audit-logs" actionLabel="Alert history →">
                  {data.all_alerts.length ? (
                    <ul>{data.all_alerts.map((row) => (
                      <AlertRow key={row.alert_id} row={row} />
                    ))}</ul>
                  ) : (
                    <p className="text-sm text-[#9ca3af]">No unread alerts. You are up to date.</p>
                  )}
                  <p className="mt-3 text-[11px] text-[#9ca3af]">{data.alerts_total} unread alert{data.alerts_total === 1 ? "" : "s"}</p>
                </Panel>
              </div>

              <div className="space-y-4">
                <Panel title="Alerts by module" actionHref="/college-admin/reports-administration" actionLabel="Report →">
                  {data.alerts_by_module.length ? (
                    <ul className="space-y-3">
                      {data.alerts_by_module.map((item) => (
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
                    <p className="text-sm text-[#9ca3af]">No module breakdown.</p>
                  )}
                </Panel>

                <Panel
                  title="Delivery channels"
                  actionHref="/college-admin/communication-administration"
                  actionLabel="Communication settings →"
                >
                  <ul className="space-y-3">
                    {data.delivery_channels.map((ch) => (
                      <li key={ch.channel_key} className="flex items-start justify-between gap-2 text-[12px]">
                        <div>
                          <p className="font-medium text-[#111827]">{ch.label}</p>
                          <p className="text-[#9ca3af]">{ch.detail}</p>
                        </div>
                        <span className="inline-flex items-center gap-1 text-[11px] text-[#047857]">
                          <CircleIcon className={cn("size-2 fill-current", !ch.enabled && "text-[#9ca3af]")} />
                          {ch.enabled ? "On" : "Off"}
                        </span>
                      </li>
                    ))}
                  </ul>
                </Panel>

                <Panel
                  title="Alert rules"
                  actionHref="/college-admin/communication-administration"
                  actionLabel="Configure →"
                >
                  <ul className="space-y-2.5">
                    {data.alert_rules.map((rule) => (
                      <li key={rule.rule_key} className="flex justify-between gap-2 text-[12px]">
                        <span className="text-[#374151]">{rule.label}</span>
                        <span className="text-right text-[#6b7280]">{rule.value_label}</span>
                      </li>
                    ))}
                  </ul>
                  <p className="mt-3 flex items-center gap-1 text-[10px] text-[#9ca3af]">
                    <Settings2Icon className="size-3" />
                    Values from institution settings
                  </p>
                </Panel>
              </div>
            </div>

          </>
        ) : null}
      </QueryState>
    </div>
  );
}