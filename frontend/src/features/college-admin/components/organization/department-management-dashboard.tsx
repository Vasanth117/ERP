"use client";

import Link from "next/link";
import { useCallback, useState } from "react";

import { CalendarDaysIcon } from "@/components/icons/erp/generated/calendar-days";
import { FilterIcon } from "@/components/icons/erp/generated/filter";
import { PlusIcon } from "@/components/icons/erp/generated/plus";
import {
  CollegeAdminDownload,
  getCollegeAdminErpIcon,
  resolveCollegeAdminIconSlug,
} from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useDepartmentManagementDashboardPage } from "@/features/college-admin/hooks/use-department-management-dashboard";
import type {
  DepartmentEnrollmentBar,
  DepartmentQuickAction,
  DepartmentSchoolBar,
} from "@/features/college-admin/types/department-management-dashboard";
import type { UserDashboardKpi } from "@/features/college-admin/types/user-management-dashboard";
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
        <span className="pointer-events-none absolute left-3 top-1/2 z-[1] -translate-y-1/2 text-[#9ca3af]">
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

function EnrollmentBarChart({ bars }: { bars: DepartmentEnrollmentBar[] }) {
  const max = Math.max(...bars.map((b) => b.student_count), 1);
  if (!bars.length) {
    return (
      <p className="py-8 text-center text-sm text-[#9ca3af]">
        No department enrollment data for the selected filters.
      </p>
    );
  }
  return (
    <div className="flex h-52 items-end justify-between gap-1 overflow-x-auto pb-2 pt-4">
      {bars.map((bar) => (
        <div
          key={bar.department_id}
          className="flex min-w-[2.5rem] flex-1 flex-col items-center gap-1.5"
          title={`${bar.student_count} students · ${bar.faculty_count} faculty`}
        >
          <span className="text-[11px] font-semibold tabular-nums text-[#374151]">
            {bar.student_count.toLocaleString("en-IN")}
          </span>
          <div
            className="w-full max-w-[48px] rounded-t-md bg-[#245dd8]"
            style={{
              height: `${Math.max(12, (bar.student_count / max) * 100)}%`,
            }}
          />
          <span className="max-w-[4rem] truncate text-center text-[10px] leading-tight text-[#6b7280]">
            {bar.department_code}
          </span>
        </div>
      ))}
    </div>
  );
}

function SchoolProgressList({ items }: { items: DepartmentSchoolBar[] }) {
  if (!items.length) {
    return <p className="py-4 text-sm text-[#9ca3af]">No schools linked to departments yet.</p>;
  }
  return (
    <ul className="space-y-4 py-2">
      {items.map((item) => (
        <li key={item.school_id || item.school_name}>
          <div className="mb-1.5 flex items-center justify-between gap-2 text-[13px]">
            <span className="font-medium text-[#111827]">{item.school_name}</span>
            <span className="tabular-nums text-[#6b7280]">{item.department_count}</span>
          </div>
          <div className="h-1.5 overflow-hidden rounded-full bg-[#f1f5f9]">
            <div
              className="h-full rounded-full bg-[#245dd8]"
              style={{ width: `${Math.min(100, Math.max(4, item.share_percent))}%` }}
            />
          </div>
        </li>
      ))}
    </ul>
  );
}

function QuickActionRow({ action }: { action: DepartmentQuickAction }) {
  const slug = resolveCollegeAdminIconSlug(action.icon_slug);
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
          <p className="text-[13px] font-medium text-[#111827]">{action.title}</p>
          <p className="text-[12px] text-[#6b7280]">{action.subtitle}</p>
        </div>
      </div>
      <Link href={action.href} className="shrink-0 text-[12px] font-medium text-[#245dd8] hover:underline">
        {action.action_label}
      </Link>
    </li>
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

export function DepartmentManagementDashboard() {
  const [academicYear, setAcademicYear] = useState("");
  const [campusId, setCampusId] = useState("");
  const [schoolId, setSchoolId] = useState("");

  const { data, isLoading, isError, error, refetch } = useDepartmentManagementDashboardPage({
    academic_year_label: academicYear || undefined,
    campus_id: campusId || undefined,
    school_id: schoolId || undefined,
  });

  const handleExport = useCallback(() => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `department-management-${new Date(data.generated_at).toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data]);

  return (
    <div className="space-y-5" data-figma-frame="69:132597">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Department Management Dashboard"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">
            {data?.page_subtitle ?? "Departments, heads, programmes and staffing at a glance"}
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <button
            type="button"
            className="inline-flex h-9 items-center gap-1.5 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb] disabled:opacity-50"
            onClick={handleExport}
            disabled={isLoading || !data}
          >
            <CollegeAdminDownload className="size-3.5" aria-hidden />
            {data?.export_label ?? "Export"}
          </button>
          <Link
            href={data?.create_department_href ?? "/college-admin/organization/create-department"}
            className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
          >
            <PlusIcon className="size-3.5" aria-hidden />
            {data?.create_department_label ?? "Create department"}
          </Link>
        </div>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between">
        <div className="flex flex-wrap items-center gap-2">
          <FilterSelect
            icon={<CalendarDaysIcon className="size-3.5" aria-hidden />}
            label={data?.academic_year_filter_label ?? "Academic year"}
            value={academicYear}
            onChange={setAcademicYear}
            options={data?.academic_year_options ?? [{ value: "", label: "Current year" }]}
          />
          <FilterSelect
            icon={<FilterIcon className="size-3.5" aria-hidden />}
            label={data?.campus_filter_label ?? "Campus"}
            value={campusId}
            onChange={setCampusId}
            options={data?.campus_options ?? [{ value: "", label: "All campuses" }]}
          />
          <FilterSelect
            label={data?.school_filter_label ?? "School"}
            value={schoolId}
            onChange={setSchoolId}
            options={data?.school_options ?? [{ value: "", label: "All schools" }]}
          />
          <span className="inline-flex items-center gap-1.5 rounded-md bg-[#eff6ff] px-2.5 py-1.5 text-[11px] font-medium text-[#1d4ed8]">
            <span className="size-1.5 rounded-full bg-[#3b82f6]" aria-hidden />
            {data?.scope_indicator_label ?? "College scope"}
          </span>
        </div>
        <p className="flex items-center gap-1.5 text-[12px] text-[#9ca3af]">
          <span className="size-1.5 rounded-full bg-[#d1d5db]" aria-hidden />
          Updated {data?.updated_at_label ?? "—"}
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

            <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_360px]">
              <div className="space-y-5">
                <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                  <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                    <h3 className="text-[14px] font-semibold text-[#111827]">{data.enrollment_chart_title}</h3>
                  </div>
                  <div className="px-5 pb-4">
                    <EnrollmentBarChart bars={data.enrollment_bars} />
                  </div>
                </section>

                <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                  <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                    <h3 className="text-[14px] font-semibold text-[#111827]">{data.attention_section_title}</h3>
                  </div>
                  {data.attention_rows.length ? (
                    <div className="overflow-x-auto">
                      <table className="w-full min-w-[36rem] text-left text-[13px]">
                        <thead>
                          <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                            {data.attention_table_headers.map((header, index) => (
                              <th
                                key={header}
                                className={cn("pb-3 font-medium", index === 0 ? "px-5" : "pr-3")}
                              >
                                {header}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-[#f1f5f9]">
                          {data.attention_rows.map((row) => (
                            <tr key={`${row.department_id}-${row.issue}`} className="hover:bg-[#f9fafb]">
                              <td className="px-5 py-3 font-medium text-[#111827]">
                                <Link href={row.detail_href} className="hover:text-[#245dd8]">
                                  {row.department_name}
                                </Link>
                              </td>
                              <td className="py-3 pr-3 text-[#374151]">{row.issue}</td>
                              <td className="py-3 pr-3 text-[#374151]">{row.owner_label}</td>
                              <td className="py-3 pr-5">
                                <StatusPill label={row.status_label} tone={row.status_tone} />
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="px-5 py-10 text-center text-sm text-[#9ca3af]">
                      No departments need attention for the current filters.
                    </p>
                  )}
                  <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
                    <span>{data.attention_footer_label}</span>
                    <Link
                      href={data.attention_view_all_href}
                      className="font-medium text-[#245dd8] hover:underline"
                    >
                      {data.attention_view_all_label}
                    </Link>
                  </div>
                </section>
              </div>

              <div className="space-y-5">
                <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                  <h3 className="mb-1 text-[14px] font-semibold text-[#111827]">{data.schools_section_title}</h3>
                  <SchoolProgressList items={data.school_bars} />
                </section>

                <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                  <h3 className="mb-1 text-[14px] font-semibold text-[#111827]">{data.quick_actions_title}</h3>
                  <ul>{data.quick_actions.map((action) => <QuickActionRow key={action.key} action={action} />)}</ul>
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