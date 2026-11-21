"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";

import { CalendarIcon } from "@/components/icons/erp/generated/calendar";
import { FilterIcon } from "@/components/icons/erp/generated/filter";
import { Button } from "@/components/ui/button";
import {
  CollegeAdminChevronDown,
  CollegeAdminDownload,
} from "@/features/college-admin/components/layout/college-admin-erp-icons";
import {
  fetchAcademicTerms,
  fetchAcademicYears,
  fetchProgrammes,
} from "@/features/college-admin/api/academics";
import { CollegeAdminDashboardKpiCard, CollegeAdminKpiGrid } from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useDepartmentPerformanceOverview } from "@/features/college-admin/hooks/use-department-performance";
import { cn } from "@/lib/utils";

const LEVEL_OPTIONS = [
  { value: "", label: "UG + PG" },
  { value: "ug", label: "Undergraduate" },
  { value: "pg", label: "Postgraduate" },
  { value: "doctoral", label: "Doctoral" },
];


function StatusPill({ statusKey, label }: { statusKey: string; label: string }) {
  const tone =
    statusKey === "on_track"
      ? "bg-[#ecfdf5] text-[#047857]"
      : statusKey === "needs_review" || statusKey === "review"
        ? "bg-[#fef2f2] text-[#b91c1c]"
        : statusKey === "action"
          ? "bg-[#eff6ff] text-[#1d4ed8]"
          : "bg-[#fff7ed] text-[#c2410c]";
  const dot =
    statusKey === "on_track"
      ? "bg-[#10b981]"
      : statusKey === "needs_review" || statusKey === "review"
        ? "bg-[#ef4444]"
        : statusKey === "action"
          ? "bg-[#3b82f6]"
          : "bg-[#f97316]";
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-medium",
        tone,
      )}
    >
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
          <Link
            href={actionHref}
            className="shrink-0 text-[12px] font-medium text-[#245dd8] hover:underline"
          >
            {actionLabel}
          </Link>
        ) : null}
      </div>
      {children}
    </section>
  );
}

function barColor(statusKey: string) {
  if (statusKey === "needs_review") return "bg-[#f97316]";
  if (statusKey === "monitor") return "bg-[#93c5fd]";
  return "bg-[#245dd8]";
}

function PassRateBarChart({
  items,
}: {
  items: { code: string; rate: number; statusKey: string }[];
}) {
  const max = Math.max(...items.map((i) => i.rate), 1);
  if (!items.length) {
    return <p className="text-sm text-[#9ca3af]">No published exam results for this term yet.</p>;
  }
  return (
    <div className="flex h-44 items-end justify-between gap-1 overflow-x-auto pb-1">
      {items.map((item) => (
        <div key={item.code} className="flex min-w-[2.25rem] flex-1 flex-col items-center gap-1">
          <span className="text-[10px] font-medium tabular-nums text-[#6b7280]">
            {item.rate.toFixed(1)}%
          </span>
          <div
            className={cn("w-full max-w-[40px] rounded-t-md", barColor(item.statusKey))}
            style={{ height: `${Math.max(10, (item.rate / max) * 100)}%` }}
          />
          <span className="max-w-[3rem] truncate text-[9px] text-[#9ca3af]">{item.code}</span>
        </div>
      ))}
    </div>
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
  onChange: (value: string) => void;
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
          "w-full cursor-pointer appearance-none truncate rounded-md border py-1.5 pr-8 text-xs outline-none",
          leadingIcon ? "pl-8" : "pl-3",
          active
            ? "border-[#245dd8] bg-[#eef4ff] font-medium text-[#245dd8]"
            : "border-[#e5e7eb] bg-white text-[#374151]",
          disabled && "opacity-60",
        )}
      >
        {children}
      </select>
      <CollegeAdminChevronDown
        className={cn(
          "pointer-events-none absolute right-2 top-1/2 size-3.5 -translate-y-1/2",
          active ? "text-[#245dd8]" : "text-[#6b7280]",
        )}
        aria-hidden
      />
    </div>
  );
}

export function DepartmentPerformanceDashboard() {
  const [academicYear, setAcademicYear] = useState("");
  const [semesterLabel, setSemesterLabel] = useState("");
  const [programmeCode, setProgrammeCode] = useState("");
  const [programmeLevel, setProgrammeLevel] = useState("");

  const yearsQ = useQuery({
    queryKey: ["college-admin", "academic-years", "dept-perf"],
    queryFn: fetchAcademicYears,
  });
  const termsQ = useQuery({
    queryKey: ["college-admin", "academic-terms", "dept-perf"],
    queryFn: () => fetchAcademicTerms(),
  });
  const programmesQ = useQuery({
    queryKey: ["college-admin", "programmes", "dept-perf"],
    queryFn: fetchProgrammes,
  });

  const queryParams = useMemo(
    () => ({
      ...(academicYear ? { academic_year_label: academicYear } : {}),
      ...(semesterLabel ? { semester_label: semesterLabel } : {}),
      ...(programmeCode ? { programme_code: programmeCode } : {}),
      ...(programmeLevel ? { programme_level: programmeLevel } : {}),
    }),
    [academicYear, semesterLabel, programmeCode, programmeLevel],
  );

  const { data, isLoading, isError, error, refetch, isFetching } =
    useDepartmentPerformanceOverview(queryParams);

  const defaultYear = useMemo(() => {
    const current = yearsQ.data?.find((y) => y.is_current)?.label;
    return current ?? data?.filters.academic_year_label ?? data?.academic_term.academic_year_label ?? "";
  }, [yearsQ.data, data]);

  const defaultSemester = useMemo(() => {
    const currentTerm = termsQ.data?.find((t) => t.is_current);
    return currentTerm?.label ?? data?.filters.semester_label ?? data?.academic_term.semester_label ?? "";
  }, [termsQ.data, data]);

  useEffect(() => {
    if (!academicYear && defaultYear) setAcademicYear(defaultYear);
  }, [academicYear, defaultYear]);

  useEffect(() => {
    if (!semesterLabel && defaultSemester) setSemesterLabel(defaultSemester);
  }, [semesterLabel, defaultSemester]);

  const semesterOptions = useMemo(() => {
    const labels = new Set<string>();
    for (const t of termsQ.data ?? []) {
      if (t.label?.trim()) labels.add(t.label.trim());
    }
    if (defaultSemester) labels.add(defaultSemester);
    if (semesterLabel) labels.add(semesterLabel);
    return Array.from(labels);
  }, [termsQ.data, defaultSemester, semesterLabel]);

  const semesterSelectValue = semesterLabel || defaultSemester || semesterOptions[0] || "";

  const semesterFilterLabel = useMemo(() => {
    if (data?.semester_display_label) return data.semester_display_label;
    if (semesterSelectValue && academicYear) {
      const yearStart = academicYear.split("-")[0];
      return `${semesterSelectValue} semester ${yearStart}`;
    }
    return semesterSelectValue || "Semester";
  }, [data?.semester_display_label, semesterSelectValue, academicYear]);

  const scorecardVisible = useMemo(
    () => (data?.scorecard ?? []).slice(0, data?.scorecard_display_limit ?? 8),
    [data?.scorecard, data?.scorecard_display_limit],
  );

  const passBars = useMemo(
    () =>
      (data?.pass_rate_by_department ?? []).map((d) => ({
        code: d.department_code,
        rate: d.pass_rate_pct ?? 0,
        statusKey: d.status_key,
      })),
    [data?.pass_rate_by_department],
  );

  const handleExport = useCallback(() => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `department-performance-${new Date(data.generated_at).toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data]);

  const kpis = data?.kpis;

  return (
    <div className="space-y-5" data-figma-frame="65:1592">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold text-[#111827]">Department performance overview</h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">
            Compare academic results, attendance and staffing across departments
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            type="button"
            className="h-9 gap-1.5 bg-[#245dd8] text-xs text-white"
            onClick={handleExport}
            disabled={!data}
          >
            <CollegeAdminDownload className="size-3.5" />
            Export
          </Button>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <FilterSelect
          value={semesterSelectValue || "__ph__"}
          onChange={setSemesterLabel}
          active={Boolean(semesterSelectValue)}
          aria-label="Semester"
          className="min-w-[12rem]"
          leadingIcon={<CalendarIcon className="size-3.5" />}
        >
          {!semesterSelectValue ? (
            <option value="__ph__" disabled>
              Semester
            </option>
          ) : null}
          {semesterOptions.map((label) => (
            <option key={label} value={label}>
              {label === semesterSelectValue ? semesterFilterLabel : label}
            </option>
          ))}
        </FilterSelect>

        <FilterSelect
          value={programmeCode}
          onChange={setProgrammeCode}
          active={Boolean(programmeCode)}
          aria-label="Programme"
          className="min-w-[11.5rem]"
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

        <FilterSelect
          value={programmeLevel}
          onChange={setProgrammeLevel}
          active={Boolean(programmeLevel)}
          aria-label="Programme level"
          className="min-w-[8.5rem]"
          leadingIcon={<FilterIcon className="size-3.5" />}
        >
          {LEVEL_OPTIONS.map((opt) => (
            <option key={opt.value || "all"} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </FilterSelect>

      </div>

      <QueryState
        isLoading={isLoading || isFetching}
        isError={isError}
        error={error}
        onRetry={() => void refetch()}
      >
        {data ? (
          <>
            <CollegeAdminKpiGrid>
              <CollegeAdminDashboardKpiCard
                label="Best pass rate"
                value={kpis?.best_pass_rate_pct != null ? `${kpis.best_pass_rate_pct}%` : "—"}
                hint={kpis?.best_pass_rate_department_name ?? "No exam results yet"}
                hintTone="success"
              />
              <CollegeAdminDashboardKpiCard
                label="Lowest pass rate"
                value={kpis?.lowest_pass_rate_pct != null ? `${kpis.lowest_pass_rate_pct}%` : "—"}
                hint={kpis?.lowest_pass_rate_department_name ?? "—"}
                hintTone="warning"
              />
              <CollegeAdminDashboardKpiCard
                label="Avg. attendance"
                value={kpis?.average_attendance_pct != null ? `${kpis.average_attendance_pct}%` : "—"}
                hint={`${kpis?.departments_above_attendance_threshold ?? 0} of ${kpis?.departments_total_for_attendance ?? 0} departments above ${kpis?.departments_attendance_threshold_pct ?? 85}%`}
              />
              <CollegeAdminDashboardKpiCard
                label="Faculty vacancies"
                value={kpis?.faculty_vacancies_total ?? 0}
                hint={`Across ${kpis?.faculty_vacancies_department_count ?? 0} departments`}
                hintTone="warning"
              />
            </CollegeAdminKpiGrid>

            <Panel
              title="Department scorecard"
              actionHref="/college-admin/organization/department-management-dashboard"
              actionLabel="Department management →"
            >
              <div className="overflow-x-auto">
                <table className="w-full min-w-[56rem] text-left text-[12px]">
                  <thead>
                    <tr className="border-b border-[#e8ecf2] text-[#6b7280]">
                      <th className="pb-2 pr-3 font-medium">Department</th>
                      <th className="pb-2 px-2 font-medium">Head of department</th>
                      <th className="pb-2 px-2 text-right font-medium">Students</th>
                      <th className="pb-2 px-2 text-right font-medium">Faculty</th>
                      <th className="pb-2 px-2 text-right font-medium">Pass %</th>
                      <th className="pb-2 px-2 text-right font-medium">Attendance</th>
                      <th className="pb-2 px-2 text-right font-medium">Avg CGPA</th>
                      <th className="pb-2 pl-2 font-medium">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {scorecardVisible.map((row) => (
                      <tr key={row.department_id} className="border-b border-[#f1f5f9]">
                        <td className="py-2.5 pr-3 font-medium text-[#111827]">{row.department_name}</td>
                        <td className="px-2 py-2.5 text-[#374151]">
                          {row.head_of_department ?? (row.head_acting ? "Acting HoD" : "—")}
                        </td>
                        <td className="px-2 py-2.5 text-right tabular-nums">{row.student_count}</td>
                        <td className="px-2 py-2.5 text-right tabular-nums">{row.faculty_count}</td>
                        <td className="px-2 py-2.5 text-right tabular-nums">
                          {row.pass_rate_pct != null ? `${row.pass_rate_pct}%` : "—"}
                        </td>
                        <td className="px-2 py-2.5 text-right tabular-nums">
                          {row.attendance_pct != null ? `${row.attendance_pct}%` : "—"}
                        </td>
                        <td className="px-2 py-2.5 text-right tabular-nums">
                          {row.average_cgpa != null ? row.average_cgpa.toFixed(2) : "—"}
                        </td>
                        <td className="py-2.5 pl-2">
                          <StatusPill statusKey={row.status_key} label={row.status_label} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="mt-3 flex flex-wrap justify-between gap-2 border-t border-[#f1f5f9] pt-3 text-[11px] text-[#6b7280]">
                <span>
                  Showing {scorecardVisible.length} of {data.scorecard_total} departments
                </span>
                <Link
                  href="/college-admin/organization/all-departments"
                  className="font-medium text-[#245dd8] hover:underline"
                >
                  View all departments →
                </Link>
              </div>
            </Panel>

            <div className="grid gap-4 xl:grid-cols-3">
              <div className="xl:col-span-2">
                <Panel
                  title="Pass percentage by department"
                  actionHref="/college-admin/dashboard/academic-analytics"
                  actionLabel="Academic analytics →"
                >
                  <PassRateBarChart items={passBars} />
                </Panel>
              </div>
              <Panel
                title="Needs attention"
                actionHref="/college-admin/organization/all-departments"
                actionLabel="View all →"
              >
                {data.needs_attention.length ? (
                  <ul className="divide-y divide-[#f1f5f9]">
                    {data.needs_attention.map((item) => (
                      <li key={`${item.department_id}-${item.message}`} className="py-3 first:pt-0">
                        <div className="flex items-start justify-between gap-2">
                          <div className="min-w-0">
                            <p className="text-[13px] font-semibold text-[#111827]">{item.department_name}</p>
                            <p className="text-[11px] text-[#9ca3af]">{item.message}</p>
                          </div>
                          <StatusPill statusKey={item.status_key} label={item.status_label} />
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-[#9ca3af]">No attention items for the selected filters.</p>
                )}
              </Panel>
            </div>

            <footer className="flex flex-wrap justify-between gap-2 border-t border-[#e8ecf2] pt-4 text-[11px] text-[#9ca3af]">
              <span>Live institutional data · Departments, exams and attendance · All times IST</span>
            </footer>
          </>
        ) : null}
      </QueryState>
    </div>
  );
}