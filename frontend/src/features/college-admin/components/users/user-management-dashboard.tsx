"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { CalendarDaysIcon } from "@/components/icons/erp/generated/calendar-days";
import { FilterIcon } from "@/components/icons/erp/generated/filter";
import { PlusIcon } from "@/components/icons/erp/generated/plus";
import { UploadIcon } from "@/components/icons/erp/generated/upload";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useUserManagementDashboardPage } from "@/features/college-admin/hooks/use-user-management-dashboard";
import type {
  UserDashboardDailyPoint,
  UserDashboardKpi,
  UserDashboardSecurityItem,
} from "@/features/college-admin/types/user-management-dashboard";
import { cn } from "@/lib/utils";

function FilterSelect({
  icon,
  label,
  value,
  onChange,
  options,
}: {
  icon?: React.ReactNode;
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <div className="relative">
      {icon ? (
        <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[#9ca3af]">
          {icon}
        </span>
      ) : null}
      <select
        aria-label={label}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={cn(
          "h-9 min-w-[9rem] rounded-md border border-[#dce3ec] bg-white pr-8 text-[13px] text-[#374151]",
          icon ? "pl-9" : "pl-3",
        )}
      >
        {options.map((opt) => (
          <option key={`${opt.value}-${opt.label}`} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
}

function StatusPill({ label, tone }: { label: string; tone: string }) {
  const styles: Record<string, string> = {
    success: "bg-[#ecfdf5] text-[#047857]",
    info: "bg-[#eff6ff] text-[#1d4ed8]",
    error: "bg-[#fef2f2] text-[#b91c1c]",
    muted: "bg-[#f3f4f6] text-[#6b7280]",
  };
  const dot: Record<string, string> = {
    success: "bg-[#10b981]",
    info: "bg-[#6366f1]",
    error: "bg-[#ef4444]",
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

function KpiCard({ kpi }: { kpi: UserDashboardKpi }) {
  const hintTone =
    kpi.hint_tone === "success"
      ? "text-[#059669]"
      : kpi.hint_tone === "warning"
        ? "text-[#d97706]"
        : kpi.hint_tone === "error"
          ? "text-[#dc2626]"
          : "text-[#9ca3af]";
  return (
    <div className="flex min-h-[7.5rem] flex-col rounded-xl border border-[#e8ecf2] bg-white p-4 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
      <p className="text-[12px] font-medium text-[#6b7280]">{kpi.label}</p>
      <p className="mt-2 text-[28px] font-bold tabular-nums tracking-tight text-[#111827]">{kpi.value}</p>
      <p className={cn("mt-auto pt-2 text-[12px]", hintTone)}>{kpi.hint_line}</p>
    </div>
  );
}

function DailyActiveChart({ points }: { points: UserDashboardDailyPoint[] }) {
  if (!points.length) {
    return <p className="text-sm text-[#9ca3af]">No login activity in this range yet.</p>;
  }
  const values = points.map((p) => p.active_users);
  const max = maxOf(values, 1);
  const min = 0;
  const span = Math.max(max - min, 1);
  const w = 480;
  const h = 160;
  const pad = 24;
  const toX = (i: number) => pad + (i * (w - 2 * pad)) / Math.max(points.length - 1, 1);
  const toY = (v: number) => h - pad - ((v - min) / span) * (h - 2 * pad);
  const line = points.map((p, i) => `${toX(i)},${toY(p.active_users)}`).join(" ");

  return (
    <div>
      <svg viewBox={`0 0 ${w} ${h}`} className="h-44 w-full">
        <line x1={pad} y1={h - pad} x2={w - pad} y2={h - pad} stroke="#e8ecf2" />
        <polyline fill="none" stroke="#245dd8" strokeWidth="2.5" points={line} />
      </svg>
      <div className="mt-1 flex justify-between gap-1 text-[9px] text-[#9ca3af]">
        {points.map((p) => (
          <span key={p.date_label} className="max-w-[2.75rem] truncate">
            {p.date_label}
          </span>
        ))}
      </div>
    </div>
  );
}

function maxOf(values: number[], floor: number) {
  return Math.max(...values, floor);
}

function SecurityCountBadge({ item }: { item: UserDashboardSecurityItem }) {
  const styles: Record<string, string> = {
    warning: "bg-[#fff7ed] text-[#c2410c]",
    info: "bg-[#eff6ff] text-[#1d4ed8]",
    error: "bg-[#fef2f2] text-[#b91c1c]",
  };
  return (
    <span className={cn("rounded-md px-2 py-0.5 text-[12px] font-semibold tabular-nums", styles[item.tone] ?? styles.info)}>
      {item.count}
    </span>
  );
}

function formatSnapshot(iso: string) {
  try {
    return new Intl.DateTimeFormat("en-IN", {
      dateStyle: "medium",
      timeStyle: "short",
      timeZone: "Asia/Kolkata",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

export function UserManagementDashboard() {
  const [dateRange, setDateRange] = useState("last_30_days");
  const [roleFilter, setRoleFilter] = useState("");
  const [departmentId, setDepartmentId] = useState("");

  const { data, isLoading, isError, error, refetch } = useUserManagementDashboardPage({
    date_range: dateRange,
    role_filter: roleFilter || undefined,
    department_id: departmentId || undefined,
  });

  useEffect(() => {
    if (data?.date_range_options?.length && !data.date_range_options.some((o) => o.value === dateRange)) {
      setDateRange(data.date_range_options[0]?.value ?? "last_30_days");
    }
  }, [data?.date_range_options, dateRange]);

  return (
    <div className="space-y-5" data-figma-frame="69:124928">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "User Management Dashboard"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">{data?.page_subtitle}</p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <Link
            href={data?.bulk_invite_href ?? "/college-admin/users/bulk-user-invitation"}
            className="inline-flex h-9 items-center gap-1.5 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb]"
          >
            <UploadIcon className="size-3.5" aria-hidden />
            {data?.bulk_invite_label ?? "Bulk invite"}
          </Link>
          <Link
            href={data?.create_user_href ?? "/college-admin/users/create-new-user"}
            className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
          >
            <PlusIcon className="size-3.5" aria-hidden />
            {data?.create_user_label ?? "Create user"}
          </Link>
        </div>
      </div>

      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-wrap items-center gap-2">
          <FilterSelect
            icon={<CalendarDaysIcon className="size-4" aria-hidden />}
            label={data?.date_range_filter_label ?? "Date range"}
            value={dateRange}
            onChange={setDateRange}
            options={data?.date_range_options ?? [{ value: "last_30_days", label: "Last 30 days" }]}
          />
          <FilterSelect
            icon={<FilterIcon className="size-4" aria-hidden />}
            label={data?.role_filter_label ?? "Role"}
            value={roleFilter}
            onChange={setRoleFilter}
            options={data?.role_options ?? [{ value: "", label: "All roles" }]}
          />
          <FilterSelect
            icon={<FilterIcon className="size-4" aria-hidden />}
            label={data?.department_filter_label ?? "Department"}
            value={departmentId}
            onChange={setDepartmentId}
            options={data?.department_options ?? [{ value: "", label: "All departments" }]}
          />
          <span className="text-[12px] font-medium text-[#245dd8]">
            <span className="mr-1 text-[#3b82f6]">•</span>
            {data?.scope_indicator_label ?? "College scope"}
          </span>
        </div>
        <p className="text-[12px] text-[#9ca3af]">
          Updated {data?.updated_at_label}
        </p>
      </div>

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              {data.kpis.map((kpi) => (
                <KpiCard key={kpi.key} kpi={kpi} />
              ))}
            </div>

            <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_320px]">
              <div className="space-y-5">
                <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                  <h3 className="mb-4 text-[14px] font-semibold text-[#111827]">{data.daily_active_title}</h3>
                  <DailyActiveChart points={data.daily_active_points} />
                </section>

                <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                  <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                    <h3 className="text-[14px] font-semibold text-[#111827]">{data.recent_accounts_title}</h3>
                  </div>
                  {data.recent_accounts.length ? (
                    <div className="overflow-x-auto">
                      <table className="w-full min-w-[36rem] text-left text-[13px]">
                        <thead>
                          <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                            <th className="px-5 pb-3 font-medium">User</th>
                            <th className="pb-3 pr-3 font-medium">Role</th>
                            <th className="pb-3 pr-3 font-medium">Department</th>
                            <th className="pb-3 pr-3 font-medium">Created</th>
                            <th className="pb-3 pr-5 font-medium">Status</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-[#f1f5f9]">
                          {data.recent_accounts.map((row) => (
                            <tr key={row.user_id} className="hover:bg-[#f9fafb]">
                              <td className="px-5 py-3 font-medium text-[#111827]">
                                <Link href={row.detail_href} className="hover:text-[#245dd8]">
                                  {row.user_name}
                                </Link>
                              </td>
                              <td className="py-3 pr-3 text-[#374151]">{row.role_label}</td>
                              <td className="py-3 pr-3 text-[#374151]">{row.department_label}</td>
                              <td className="py-3 pr-3 tabular-nums text-[#374151]">{row.created_label}</td>
                              <td className="py-3 pr-5">
                                <StatusPill label={row.status_label} tone={row.status_tone} />
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="px-5 py-8 text-sm text-[#9ca3af]">No new accounts in this period.</p>
                  )}
                  <div className="flex items-center justify-between border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
                    <span>{data.recent_accounts_footer_label}</span>
                    <Link href={data.view_all_href} className="font-medium text-[#245dd8] hover:underline">
                      {data.view_all_label}
                    </Link>
                  </div>
                </section>
              </div>

              <div className="space-y-5">
                <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                  <h3 className="mb-4 text-[14px] font-semibold text-[#111827]">{data.accounts_by_role_title}</h3>
                  {data.role_bars.length ? (
                    <ul className="space-y-3.5">
                      {data.role_bars.map((row) => (
                        <li key={row.key}>
                          <div className="mb-1 flex justify-between text-[13px]">
                            <span className="text-[#374151]">{row.label}</span>
                            <span className="font-medium tabular-nums text-[#111827]">{row.count}</span>
                          </div>
                          <div className="h-2 overflow-hidden rounded-full bg-[#f1f5f9]">
                            <div
                              className="h-full rounded-full bg-[#245dd8]"
                              style={{ width: `${row.progress_percent}%` }}
                            />
                          </div>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm text-[#9ca3af]">No accounts yet.</p>
                  )}
                </section>

                <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                  <div className="flex items-center justify-between border-b border-[#f1f5f9] px-5 py-3.5">
                    <h3 className="text-[14px] font-semibold text-[#111827]">{data.security_checks_title}</h3>
                    <Link
                      href={data.security_audit_href}
                      className="text-[12px] font-medium text-[#245dd8] hover:underline"
                    >
                      {data.security_audit_label}
                    </Link>
                  </div>
                  <ul className="divide-y divide-[#f1f5f9] px-5">
                    {data.security_items.map((item) => (
                      <li key={item.key} className="flex items-start justify-between gap-3 py-3.5">
                        <div>
                          <p className="text-[13px] font-medium text-[#111827]">{item.title}</p>
                          <p className="text-[12px] text-[#6b7280]">{item.description}</p>
                        </div>
                        <SecurityCountBadge item={item} />
                      </li>
                    ))}
                  </ul>
                </section>
              </div>
            </div>

            <footer className="flex flex-col gap-2 border-t border-[#e8ecf2] pt-4 text-[11px] text-[#9ca3af] sm:flex-row sm:items-center sm:justify-between">
              <p>{data.footer_disclaimer}</p>
              <p className="tabular-nums">
                {data.footer_snapshot_label} · {formatSnapshot(data.generated_at)}
              </p>
            </footer>
          </>
        ) : null}
      </QueryState>
    </div>
  );
}