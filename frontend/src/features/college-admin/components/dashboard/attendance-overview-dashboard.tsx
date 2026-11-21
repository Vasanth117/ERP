"use client";

import Link from "next/link";
import { useCallback, useMemo, useState, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";

import { FilterIcon } from "@/components/icons/erp/generated/filter";
import { MailIcon } from "@/components/icons/erp/generated/mail";
import { Button } from "@/components/ui/button";
import {
  CollegeAdminChevronDown,
  CollegeAdminDownload,
} from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { fetchDepartments } from "@/features/college-admin/api/organization";
import { fetchProgrammes } from "@/features/college-admin/api/academics";
import { CollegeAdminDashboardKpiCard, CollegeAdminKpiGrid } from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useAttendanceOverview } from "@/features/college-admin/hooks/use-attendance-overview";
import type { DashboardDateRange } from "@/features/college-admin/types/dashboard";
import { cn } from "@/lib/utils";

const RANGE_OPTIONS: { value: DashboardDateRange; label: string }[] = [
  { value: "today", label: "Today" },
  { value: "week", label: "This week" },
  { value: "month", label: "Last 30 days" },
  { value: "semester", label: "This semester" },
];


function StatusPill({ statusKey, label }: { statusKey: string; label: string }) {
  const tone =
    statusKey === "healthy"
      ? "bg-[#ecfdf5] text-[#047857]"
      : statusKey === "at_risk"
        ? "bg-[#fef2f2] text-[#b91c1c]"
        : "bg-[#fff7ed] text-[#c2410c]";
  const dot =
    statusKey === "healthy" ? "bg-[#10b981]" : statusKey === "at_risk" ? "bg-[#ef4444]" : "bg-[#f97316]";
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-medium", tone)}>
      <span className={cn("size-1.5 rounded-full", dot)} />
      {label}
    </span>
  );
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

function DailyAttendanceChart({ points }: { points: { label: string; rate: number | null }[] }) {
  if (!points.length) {
    return <p className="text-sm text-[#9ca3af]">No submitted attendance sessions in this range yet.</p>;
  }
  const values = points.map((p) => p.rate).filter((v): v is number => v != null);
  const min = Math.min(...values, 70);
  const max = Math.max(...values, 100);
  const span = Math.max(max - min, 8);
  const w = 480;
  const h = 160;
  const pad = 24;
  const toX = (i: number) => pad + (i * (w - 2 * pad)) / Math.max(points.length - 1, 1);
  const toY = (v: number) => h - pad - ((v - min) / span) * (h - 2 * pad);
  const line = points
    .map((p, i) => (p.rate != null ? `${toX(i)},${toY(p.rate)}` : null))
    .filter(Boolean)
    .join(" ");

  return (
    <div>
      <svg viewBox={`0 0 ${w} ${h}`} className="h-40 w-full">
        <line x1={pad} y1={h - pad} x2={w - pad} y2={h - pad} stroke="#e8ecf2" />
        {line ? <polyline fill="none" stroke="#245dd8" strokeWidth="2.5" points={line} /> : null}
      </svg>
      <div className="mt-1 flex justify-between text-[9px] text-[#9ca3af]">
        {points.map((p) => (
          <span key={p.label} className="max-w-[2.5rem] truncate">
            {p.label}
          </span>
        ))}
      </div>
    </div>
  );
}

function YearAttendanceBars({ items }: { items: { label: string; rate: number | null }[] }) {
  if (!items.length) {
    return <p className="text-sm text-[#9ca3af]">No year-wise attendance for the current filters.</p>;
  }
  const max = Math.max(...items.map((i) => i.rate ?? 0), 1);
  return (
    <ul className="space-y-3">
      {items.map((item) => (
        <li key={item.label}>
          <div className="mb-1 flex justify-between text-[12px]">
            <span className="text-[#374151]">{item.label}</span>
            <span className="tabular-nums text-[#6b7280]">{item.rate != null ? `${item.rate}%` : "—"}</span>
          </div>
          <div className="h-2 rounded-full bg-[#eef2f7]">
            <div
              className="h-full rounded-full bg-[#245dd8]"
              style={{ width: `${item.rate != null ? Math.max(4, (item.rate / max) * 100) : 4}%` }}
            />
          </div>
        </li>
      ))}
    </ul>
  );
}

function CountBadge({ bucketKey, count }: { bucketKey: string; count: number }) {
  const tone =
    bucketKey === "pending_review"
      ? "bg-[#eff6ff] text-[#1d4ed8]"
      : bucketKey === "awaiting_hod"
        ? "bg-[#fff7ed] text-[#c2410c]"
        : bucketKey === "approved_week"
          ? "bg-[#ecfdf5] text-[#047857]"
          : bucketKey === "detention_risk"
            ? "bg-[#fef2f2] text-[#b91c1c]"
            : "bg-[#fff7ed] text-[#c2410c]";
  return (
    <span className={cn("rounded-full px-2.5 py-0.5 text-[12px] font-semibold tabular-nums", tone)}>{count}</span>
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

export function AttendanceOverviewDashboard() {
  const [dateRange, setDateRange] = useState<DashboardDateRange>("month");
  const [departmentId, setDepartmentId] = useState("");
  const [programmeCode, setProgrammeCode] = useState("");

  const departmentsQ = useQuery({ queryKey: ["ca", "departments", "attendance"], queryFn: fetchDepartments });
  const programmesQ = useQuery({ queryKey: ["ca", "programmes", "attendance"], queryFn: fetchProgrammes });

  const queryParams = useMemo(
    () => ({
      range: dateRange,
      ...(departmentId ? { department_id: departmentId } : {}),
      ...(programmeCode ? { programme_code: programmeCode } : {}),
    }),
    [dateRange, departmentId, programmeCode],
  );

  const { data, isLoading, isError, error, refetch, isFetching } = useAttendanceOverview(queryParams);

  const rangeLabel = data?.range_display_label ?? RANGE_OPTIONS.find((o) => o.value === dateRange)?.label ?? "Last 30 days";

  const handleExport = useCallback(() => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `attendance-overview-${new Date(data.generated_at).toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data]);

  const chartPoints = useMemo(
    () =>
      (data?.daily_student_attendance ?? []).map((p) => ({
        label: p.label,
        rate: p.attendance_pct,
      })),
    [data?.daily_student_attendance],
  );

  const yearBars = useMemo(
    () =>
      (data?.attendance_by_year ?? []).map((y) => ({
        label: y.label,
        rate: y.attendance_pct,
      })),
    [data?.attendance_by_year],
  );

  const kpis = data?.kpis;

  return (
    <div className="space-y-5" data-figma-frame="66:2485">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold text-[#111827]">Attendance overview</h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">Student and faculty attendance for the current semester</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link
            href="/college-admin/attendance-administration/shortages"
            className="inline-flex h-9 items-center gap-1.5 rounded-md border border-[#e5e7eb] bg-white px-3 text-xs font-medium text-[#374151] hover:bg-[#f9fafb]"
          >
            <MailIcon className="size-3.5" />
            Send shortage alerts
          </Link>
          <Button type="button" className="h-9 gap-1.5 bg-[#245dd8] text-xs text-white" onClick={handleExport} disabled={!data}>
            <CollegeAdminDownload className="size-3.5" />
            Export
          </Button>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <FilterSelect
          value={dateRange}
          onChange={(v) => setDateRange(v as DashboardDateRange)}
          active
          aria-label="Date range"
          className="min-w-[9.5rem]"
        >
          {RANGE_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.value === dateRange ? rangeLabel : o.label}
            </option>
          ))}
        </FilterSelect>
        <FilterSelect
          value={departmentId}
          onChange={setDepartmentId}
          active={Boolean(departmentId)}
          aria-label="Department"
          className="min-w-[11rem]"
          leadingIcon={<FilterIcon className="size-3.5" />}
          disabled={departmentsQ.isLoading}
        >
          <option value="">All departments</option>
          {(departmentsQ.data ?? []).map((d) => (
            <option key={d.department_id} value={d.department_id}>
              {d.name}
            </option>
          ))}
        </FilterSelect>
        <FilterSelect
          value={programmeCode}
          onChange={setProgrammeCode}
          active={Boolean(programmeCode)}
          aria-label="Programme"
          className="min-w-[11rem]"
          leadingIcon={<FilterIcon className="size-3.5" />}
          disabled={programmesQ.isLoading}
        >
          <option value="">All programmes</option>
          {(programmesQ.data ?? []).map((p) => (
            <option key={p.programme_id} value={p.code ?? p.name}>
              {p.name}
            </option>
          ))}
        </FilterSelect>
      </div>

      <QueryState isLoading={isLoading || isFetching} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            <CollegeAdminKpiGrid>
              <CollegeAdminDashboardKpiCard
                label="Today’s student attendance"
                value={kpis?.today_student_attendance_pct != null ? `${kpis.today_student_attendance_pct}%` : "—"}
                hint={`${kpis?.today_students_present ?? 0} of ${kpis?.today_students_total ?? 0} present`}
              />
              <CollegeAdminDashboardKpiCard
                label="Semester average"
                value={kpis?.semester_average_pct != null ? `${kpis.semester_average_pct}%` : "—"}
                hint={`Target ${kpis?.semester_target_pct ?? 85}% · minimum ${kpis?.semester_minimum_pct ?? 75}%`}
              />
              <CollegeAdminDashboardKpiCard
                label={`Below ${kpis?.semester_minimum_pct ?? 75}%`}
                value={kpis?.students_below_minimum ?? 0}
                hint="Condonation risk"
                hintTone="danger"
              />
              <CollegeAdminDashboardKpiCard
                label="Today’s faculty attendance"
                value={kpis?.today_faculty_attendance_pct != null ? `${kpis.today_faculty_attendance_pct}%` : "—"}
                hint={`${kpis?.today_faculty_present ?? 0} of ${kpis?.today_faculty_total ?? 0} present`}
              />
            </CollegeAdminKpiGrid>

            <div className="grid gap-4 xl:grid-cols-3">
              <div className="space-y-4 xl:col-span-2">
                <Panel
                  title="Daily student attendance"
                  actionHref="/college-admin/attendance-administration"
                  actionLabel="Attendance administration →"
                >
                  <DailyAttendanceChart points={chartPoints} />
                </Panel>
                <Panel
                  title="Department-wise attendance"
                  actionHref="/college-admin/attendance-administration/summaries/departments"
                  actionLabel="View all departments →"
                >
                  {data.department_rows.length ? (
                    <>
                      <div className="overflow-x-auto">
                        <table className="w-full min-w-[40rem] text-left text-[12px]">
                          <thead>
                            <tr className="border-b border-[#e8ecf2] text-[#6b7280]">
                              <th className="pb-2 pr-2 font-medium">Department</th>
                              <th className="pb-2 px-2 text-right font-medium">Students</th>
                              <th className="pb-2 px-2 text-right font-medium">Today (%)</th>
                              <th className="pb-2 px-2 text-right font-medium">Semester avg (%)</th>
                              <th className="pb-2 px-2 text-right font-medium">Below {kpis?.semester_minimum_pct ?? 75}%</th>
                              <th className="pb-2 pl-2 font-medium">Status</th>
                            </tr>
                          </thead>
                          <tbody>
                            {data.department_rows.map((row) => (
                              <tr key={row.department_id} className="border-b border-[#f1f5f9]">
                                <td className="py-2 pr-2 font-medium text-[#111827]">{row.department_name}</td>
                                <td className="px-2 py-2 text-right tabular-nums">{row.student_count}</td>
                                <td className="px-2 py-2 text-right tabular-nums">
                                  {row.today_pct != null ? `${row.today_pct}%` : "—"}
                                </td>
                                <td className="px-2 py-2 text-right tabular-nums">
                                  {row.semester_avg_pct != null ? `${row.semester_avg_pct}%` : "—"}
                                </td>
                                <td className="px-2 py-2 text-right tabular-nums">{row.below_minimum_count}</td>
                                <td className="py-2 pl-2">
                                  <StatusPill statusKey={row.status_key} label={row.status_label} />
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                      <p className="mt-3 border-t border-[#f1f5f9] pt-3 text-[11px] text-[#6b7280]">
                        Showing {data.department_rows.length} of {data.department_rows_total} departments
                      </p>
                    </>
                  ) : (
                    <p className="text-sm text-[#9ca3af]">No department attendance data for the current term.</p>
                  )}
                </Panel>
              </div>
              <div className="space-y-4">
                <Panel title="Attendance by year">
                  <YearAttendanceBars items={yearBars} />
                </Panel>
                <Panel title="Correction requests" actionHref="/college-admin/attendance-administration/corrections" actionLabel="View all →">
                  <ul className="divide-y divide-[#f1f5f9]">
                    {data.correction_requests.map((item) => (
                      <li key={item.bucket_key} className="flex items-center justify-between gap-2 py-3 first:pt-0">
                        <p className="text-[13px] font-semibold text-[#111827]">{item.label}</p>
                        <CountBadge bucketKey={item.bucket_key} count={item.count} />
                      </li>
                    ))}
                  </ul>
                </Panel>
                <Panel title="Shortage alerts" actionHref="/college-admin/attendance-administration/shortages" actionLabel="View shortage report →">
                  <ul className="divide-y divide-[#f1f5f9]">
                    {data.shortage_alerts.map((item) => (
                      <li key={item.alert_key} className="flex items-center justify-between gap-2 py-3 first:pt-0">
                        <p className="text-[13px] text-[#374151]">{item.label}</p>
                        <CountBadge bucketKey={item.alert_key} count={item.count} />
                      </li>
                    ))}
                  </ul>
                </Panel>
              </div>
            </div>

            <footer className="flex flex-wrap justify-between gap-2 border-t border-[#e8ecf2] pt-4 text-[11px] text-[#9ca3af]">
              <span>Live institutional data · Student and faculty attendance · All times IST</span>
            </footer>
          </>
        ) : null}
      </QueryState>
    </div>
  );
}