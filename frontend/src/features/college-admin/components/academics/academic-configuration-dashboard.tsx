"use client";

import Link from "next/link";

import { CalendarDaysIcon } from "@/components/icons/erp/generated/calendar-days";
import { ListChecksIcon } from "@/components/icons/erp/generated/list-checks";
import { TriangleAlertIcon } from "@/components/icons/erp/generated/triangle-alert";
import {
  getCollegeAdminErpIcon,
  resolveCollegeAdminIconSlug,
} from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { CollegeAdminUserDashboardKpiCard, CollegeAdminKpiGrid } from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useAcademicConfigurationDashboardPage } from "@/features/college-admin/hooks/use-academic-configuration-dashboard";
import type {
  AcademicConfigShortcut,
  AcademicConfigSetupAlert,
  AcademicConfigAreaRow,
  AcademicRegulationUsageItem,
} from "@/features/college-admin/types/academic-configuration-dashboard";
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

function SetupAlertBanner({ alert }: { alert: AcademicConfigSetupAlert }) {
  return (
    <div className="flex flex-col gap-2 rounded-xl border border-[#fde68a] bg-[#fffbeb] p-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex gap-3">
        <TriangleAlertIcon className="mt-0.5 size-5 shrink-0 text-[#d97706]" aria-hidden />
        <div>
          <p className="text-[13px] font-semibold text-[#92400e]">{alert.title}</p>
          <p className="mt-1 text-[12px] text-[#a16207]">{alert.description}</p>
        </div>
      </div>
      <Link href={alert.continue_href} className="shrink-0 text-[12px] font-medium text-[#245dd8] hover:underline">
        {alert.continue_label}
      </Link>
    </div>
  );
}

function RegulationBar({ item }: { item: AcademicRegulationUsageItem }) {
  const barColor =
    item.tone === "phasing_out"
      ? "bg-[#b45309]"
      : item.tone === "current"
        ? "bg-[#245dd8]"
        : "bg-[#3b82f6]";
  return (
    <li>
      <div className="mb-1.5 flex items-center justify-between gap-2 text-[13px]">
        <span className="font-medium text-[#111827]">{item.regulation_label}</span>
        <span className="tabular-nums text-[#6b7280]">{item.student_count.toLocaleString("en-IN")} students</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-[#f1f5f9]">
        <div
          className={cn("h-full rounded-full", barColor)}
          style={{ width: `${Math.min(100, Math.max(4, item.share_percent))}%` }}
        />
      </div>
    </li>
  );
}

function ShortcutRow({ item }: { item: AcademicConfigShortcut }) {
  const slug = resolveCollegeAdminIconSlug(item.icon_slug);
  const Icon = getCollegeAdminErpIcon(slug);
  return (
    <li className="flex items-start justify-between gap-3 border-b border-[#f1f5f9] py-3.5 last:border-0">
      <div className="flex min-w-0 gap-3">
        {Icon ? (
          <Icon className="mt-0.5 size-[18px] shrink-0 text-[#9ca3af]" aria-hidden />
        ) : (
          <span className="mt-1 size-[18px] shrink-0 rounded bg-[#f3f4f6]" aria-hidden />
        )}
        <div className="min-w-0">
          <p className="text-[13px] font-medium text-[#111827]">{item.title}</p>
          <p className="text-[12px] text-[#6b7280]">{item.subtitle}</p>
        </div>
      </div>
      <Link href={item.href} className="shrink-0 text-[12px] font-medium text-[#245dd8] hover:underline">
        {item.action_label}
      </Link>
    </li>
  );
}

function ConfigAreaTable({
  headers,
  rows,
  footerLabel,
  checklistHref,
  checklistLabel,
}: {
  headers: string[];
  rows: AcademicConfigAreaRow[];
  footerLabel: string;
  checklistHref: string;
  checklistLabel: string;
}) {
  if (!rows.length) {
    return (
      <p className="px-5 py-10 text-center text-sm text-[#9ca3af]">No configuration areas recorded yet.</p>
    );
  }
  return (
    <>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[40rem] text-left text-[13px]">
          <thead>
            <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
              {headers.map((header, index) => (
                <th key={header} className={cn("pb-3 font-medium", index === 0 ? "px-5" : "pr-3")}>
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-[#f1f5f9]">
            {rows.map((row) => (
              <tr key={row.area_key} className="hover:bg-[#f9fafb]">
                <td className="px-5 py-3 font-medium text-[#111827]">
                  <Link href={row.detail_href} className="hover:text-[#245dd8]">
                    {row.area_label}
                  </Link>
                </td>
                <td className="py-3 pr-3 text-[#374151]">{row.owner_label}</td>
                <td className="py-3 pr-3 tabular-nums text-[#374151]">{row.last_updated_label}</td>
                <td className="py-3 pr-3 tabular-nums font-medium text-[#111827]">{row.progress_percent}%</td>
                <td className="py-3 pr-5">
                  <StatusPill label={row.status_label} tone={row.status_tone} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
        <span>{footerLabel}</span>
        <Link href={checklistHref} className="font-medium text-[#245dd8] hover:underline">
          {checklistLabel}
        </Link>
      </div>
    </>
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

export function AcademicConfigurationDashboard() {
  const { data, isLoading, isError, error, refetch } = useAcademicConfigurationDashboardPage();

  return (
    <div className="space-y-5" data-figma-frame="69:139646">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Academic Configuration Dashboard"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">
            {data?.page_subtitle ?? "Status of academic years, programmes, curricula and grading rules"}
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <Link
            href={data?.checklist_href ?? "/college-admin/academics/academic-configuration-history"}
            className="inline-flex h-9 items-center gap-1.5 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb]"
          >
            <ListChecksIcon className="size-3.5" aria-hidden />
            {data?.checklist_label ?? "Configuration checklist"}
          </Link>
          <Link
            href={data?.open_current_year_href ?? "/college-admin/academics/academic-year-management"}
            className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
          >
            <CalendarDaysIcon className="size-3.5" aria-hidden />
            {data?.open_current_year_label ?? "Open current year"}
          </Link>
        </div>
      </div>

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            <CollegeAdminKpiGrid>
              {data.kpis.map((kpi, index) => (
                <CollegeAdminUserDashboardKpiCard key={kpi.key} kpi={kpi} index={index} />
              ))}
            </CollegeAdminKpiGrid>

            {data.setup_alert ? <SetupAlertBanner alert={data.setup_alert} /> : null}

            <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_360px]">
              <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                  <h3 className="text-[14px] font-semibold text-[#111827]">{data.config_section_title}</h3>
                </div>
                <ConfigAreaTable
                  headers={data.config_table_headers}
                  rows={data.config_area_rows}
                  footerLabel={data.config_footer_count_label}
                  checklistHref={data.config_checklist_href}
                  checklistLabel={data.config_checklist_label}
                />
              </section>

              <div className="space-y-5">
                <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                  <h3 className="mb-4 text-[14px] font-semibold text-[#111827]">{data.regulations_section_title}</h3>
                  {data.regulation_items.length ? (
                    <ul className="space-y-4">{data.regulation_items.map((item) => <RegulationBar key={item.regulation_key} item={item} />)}</ul>
                  ) : (
                    <p className="text-sm text-[#9ca3af]">No student regulation mapping yet. Publish programme curricula.</p>
                  )}
                </section>

                <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                  <h3 className="mb-1 text-[14px] font-semibold text-[#111827]">{data.shortcuts_section_title}</h3>
                  <ul>{data.shortcuts.map((item) => <ShortcutRow key={item.key} item={item} />)}</ul>
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