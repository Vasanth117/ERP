"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { toast } from "sonner";

import { CalendarIcon } from "@/components/icons/erp/generated/calendar";
import { ListFilterIcon } from "@/components/icons/erp/generated/list-filter";
import { MapPinIcon } from "@/components/icons/erp/generated/map-pin";
import { CollegeAdminDownload } from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useDownloadLoginAccountActivity,
  useLoginAccountActivityPage,
} from "@/features/college-admin/hooks/use-login-account-activity";
import type { UserDashboardKpi } from "@/features/college-admin/types/user-management-dashboard";
import { cn } from "@/lib/utils";

function KpiCard({ kpi }: { kpi: UserDashboardKpi }) {
  const hintTone =
    kpi.hint_tone === "success"
      ? "text-[#059669]"
      : kpi.hint_tone === "warning"
        ? "text-[#d97706]"
        : "text-[#9ca3af]";
  return (
    <div className="flex min-h-[7.5rem] flex-col rounded-xl border border-[#e8ecf2] bg-white p-4 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
      <p className="text-[12px] font-medium text-[#6b7280]">{kpi.label}</p>
      <p className="mt-2 text-[28px] font-bold tabular-nums tracking-tight text-[#111827]">{kpi.value}</p>
      <p className={cn("mt-auto pt-2 text-[12px]", hintTone)}>{kpi.hint_line}</p>
    </div>
  );
}

function ResultPill({ label, tone }: { label: string; tone: string }) {
  const styles: Record<string, string> = {
    success: "bg-[#ecfdf5] text-[#047857]",
    warning: "bg-[#fff7ed] text-[#c2410c]",
    error: "bg-[#fef2f2] text-[#b91c1c]",
    muted: "bg-[#f3f4f6] text-[#6b7280]",
  };
  return (
    <span className={cn("inline-flex rounded-full px-2.5 py-0.5 text-[11px] font-medium", styles[tone] ?? styles.muted)}>
      {label}
    </span>
  );
}

function FilterSelect({
  icon,
  label,
  value,
  onChange,
  options,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <div className="relative">
      <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[#9ca3af]">{icon}</span>
      <select
        aria-label={label}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="h-9 min-w-[8.5rem] appearance-none rounded-md border border-[#dce3ec] bg-white pl-9 pr-8 text-[13px] text-[#374151]"
      >
        {options.map((opt) => (
          <option key={opt.value || "all"} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
}

export function LoginAccountActivityDashboard() {
  const [dateRange, setDateRange] = useState("last_7_days");
  const [roleFilter, setRoleFilter] = useState("");
  const [locationFilter, setLocationFilter] = useState("");

  const params = {
    date_range: dateRange,
    role_filter: roleFilter || undefined,
    location_filter: locationFilter || undefined,
  };
  const pageQuery = useLoginAccountActivityPage(params);
  const downloadMutation = useDownloadLoginAccountActivity(params);

  const data = pageQuery.data;

  useEffect(() => {
    if (data?.selected_date_range) setDateRange(data.selected_date_range);
  }, [data?.selected_date_range]);

  const maxBar = Math.max(data?.daily_bars_max ?? 1, 1);

  return (
    <div className="space-y-5" data-figma-frame="69:127724">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Login & Account Activity"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">{data?.page_subtitle}</p>
        </div>
        <button
          type="button"
          disabled={!data || downloadMutation.isPending}
          onClick={() =>
            downloadMutation.mutate(undefined, {
              onError: (e: Error) => toast.error(e.message),
            })
          }
          className="inline-flex h-9 shrink-0 items-center gap-1.5 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb] disabled:opacity-50"
        >
          <CollegeAdminDownload className="size-3.5" aria-hidden />
          {data?.export_label ?? "Export"}
        </button>
      </div>

      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-wrap items-center gap-2">
          <FilterSelect
            icon={<CalendarIcon className="size-3.5" />}
            label="Time range"
            value={dateRange}
            onChange={setDateRange}
            options={data?.date_range_options ?? [{ value: "last_7_days", label: "Last 7 days" }]}
          />
          <FilterSelect
            icon={<ListFilterIcon className="size-3.5" />}
            label="Role"
            value={roleFilter}
            onChange={setRoleFilter}
            options={data?.role_filter_options ?? [{ value: "", label: "All roles" }]}
          />
          <FilterSelect
            icon={<MapPinIcon className="size-3.5" />}
            label="Location"
            value={locationFilter}
            onChange={setLocationFilter}
            options={data?.location_filter_options ?? [{ value: "", label: "All locations" }]}
          />
          <span className="inline-flex items-center gap-1.5 rounded-full border border-[#dce3ec] bg-white px-3 py-1 text-[11px] font-medium text-[#374151]">
            <span className="size-1.5 rounded-full bg-[#10b981]" />
            {data?.scope_badge_label ?? "College scope"}
          </span>
        </div>
        <p className="text-[12px] text-[#9ca3af]">{data?.updated_label}</p>
      </div>

      <QueryState query={pageQuery}>
        {data ? (
          <>
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              {data.kpis.map((kpi) => (
                <KpiCard key={kpi.key} kpi={kpi} />
              ))}
            </div>

            <div className="grid gap-5 lg:grid-cols-3">
              <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)] lg:col-span-2">
                <h3 className="mb-4 text-[14px] font-semibold text-[#111827]">{data.logins_per_day_title}</h3>
                {data.daily_bars.length ? (
                  <div className="flex h-48 items-end justify-between gap-2 border-b border-[#e8ecf2] pb-2">
                    {data.daily_bars.map((bar) => (
                      <div key={bar.day_key} className="flex min-w-0 flex-1 flex-col items-center gap-1">
                        <span className="text-[10px] font-medium tabular-nums text-[#6b7280]">{bar.login_count}</span>
                        <div
                          className="w-full max-w-[3rem] rounded-t bg-[#245dd8]"
                          style={{ height: `${Math.max(8, (bar.login_count / maxBar) * 140)}px` }}
                        />
                        <span className="text-[11px] font-medium text-[#374151]">{bar.day_label}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-[#9ca3af]">No login data in this range yet.</p>
                )}
              </section>

              <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <h3 className="mb-4 text-[14px] font-semibold text-[#111827]">{data.login_methods_title}</h3>
                <ul className="space-y-4">
                  {data.method_bars.map((row) => (
                    <li key={row.method_key}>
                      <div className="mb-1 flex justify-between text-[12px]">
                        <span className="text-[#374151]">{row.method_label}</span>
                        <span className="font-medium tabular-nums text-[#111827]">{row.percent}%</span>
                      </div>
                      <div className="h-2 overflow-hidden rounded-full bg-[#f1f5f9]">
                        <div className="h-full rounded-full bg-[#245dd8]" style={{ width: `${row.percent}%` }} />
                      </div>
                    </li>
                  ))}
                </ul>
              </section>
            </div>

            <div className="grid gap-5 lg:grid-cols-3">
              <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)] lg:col-span-2">
                <div className="flex items-center justify-between border-b border-[#f1f5f9] px-5 py-3.5">
                  <div className="flex items-center gap-2">
                    <h3 className="text-[14px] font-semibold text-[#111827]">{data.recent_section_title}</h3>
                    <span className="rounded-full bg-[#ecfdf5] px-2 py-0.5 text-[10px] font-medium text-[#047857]">
                      {data.recent_live_label}
                    </span>
                  </div>
                  <Link href={data.view_all_href} className="text-[12px] font-medium text-[#245dd8] hover:underline">
                    {data.view_all_label} →
                  </Link>
                </div>
                {data.recent_rows.length ? (
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[36rem] text-left text-[13px]">
                      <thead>
                        <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                          {data.recent_table_headers.map((h, i) => (
                            <th key={h} className={cn("pb-3 font-medium", i === 0 ? "px-5" : "pr-3")}>
                              {h}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {data.recent_rows.map((row, idx) => (
                          <tr key={`${row.user_name}-${idx}`} className="border-t border-[#f1f5f9]">
                            <td className="px-5 py-3 font-medium text-[#111827]">{row.user_name}</td>
                            <td className="py-3 pr-3 text-[#374151]">{row.method_label}</td>
                            <td className="py-3 pr-3 text-[#6b7280]">{row.device_label}</td>
                            <td className="py-3 pr-3 text-[#6b7280]">{row.location_label}</td>
                            <td className="py-3 pr-3">
                              <ResultPill label={row.result_label} tone={row.result_tone} />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="px-5 py-8 text-sm text-[#9ca3af]">No sign-ins recorded for this range.</p>
                )}
              </section>

              <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <div className="flex items-center justify-between border-b border-[#f1f5f9] px-5 py-3.5">
                  <h3 className="text-[14px] font-semibold text-[#111827]">{data.locked_section_title}</h3>
                  <Link
                    href="/college-admin/users/user-account-activation-suspension?tab=suspended"
                    className="text-[12px] font-medium text-[#245dd8] hover:underline"
                  >
                    {data.unlock_label} →
                  </Link>
                </div>
                <ul className="divide-y divide-[#f1f5f9] px-5">
                  {data.locked_accounts.length ? (
                    data.locked_accounts.map((card) => (
                      <li key={`${card.user_id}-${card.user_name}`} className="py-3">
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <p className="text-[13px] font-medium text-[#111827]">{card.user_name}</p>
                            <p className="mt-0.5 text-[11px] text-[#6b7280]">{card.subtitle}</p>
                          </div>
                          <ResultPill label={card.status_label} tone={card.status_tone} />
                        </div>
                        <Link href={card.unlock_href} className="mt-2 inline-block text-[11px] text-[#245dd8] hover:underline">
                          {data.unlock_label}
                        </Link>
                      </li>
                    ))
                  ) : (
                    <li className="py-6 text-sm text-[#9ca3af]">No locked accounts right now.</li>
                  )}
                </ul>
              </section>
            </div>

            <footer className="flex flex-col gap-1 border-t border-[#e8ecf2] pt-4 text-[11px] text-[#9ca3af] sm:flex-row sm:items-center sm:justify-between">
              <p>{data.footer_disclaimer}</p>
              <p>{data.footer_snapshot_label}</p>
            </footer>
          </>
        ) : null}
      </QueryState>
    </div>
  );
}