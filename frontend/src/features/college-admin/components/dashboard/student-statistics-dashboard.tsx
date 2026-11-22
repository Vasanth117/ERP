"use client";

import Link from "next/link";
import { CollegeAdminDashboardPanel as Panel } from "@/features/college-admin/components/ui/dashboard-panel-ui";
import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { CalendarIcon } from "@/components/icons/erp/generated/calendar";
import { FilterIcon } from "@/components/icons/erp/generated/filter";
import { Button } from "@/components/ui/button";
import {
  CollegeAdminChevronDown,
  CollegeAdminDownload,
} from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { fetchAcademicYears, fetchProgrammes } from "@/features/college-admin/api/academics";
import { CollegeAdminDashboardKpiCard, CollegeAdminKpiGrid } from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { QueryState, StatCard } from "@/features/college-admin/components/ui/query-state";
import { useStudentStatisticsOverview } from "@/features/college-admin/hooks/use-student-statistics";
import type { DistributionItem } from "@/features/college-admin/types/student-statistics";
import { cn } from "@/lib/utils";

const STUDY_YEAR_OPTIONS = [
  { value: "", label: "All years" },
  { value: "1", label: "Year 1" },
  { value: "2", label: "Year 2" },
  { value: "3", label: "Year 3" },
  { value: "4", label: "Year 4" },
];



function DepartmentBarChart({
  items,
}: {
  items: { label: string; count: number }[];
}) {
  const max = Math.max(...items.map((i) => i.count), 1);
  if (!items.length) {
    return <p className="text-sm text-[#9ca3af]">No department enrolment data yet.</p>;
  }
  return (
    <div className="flex h-44 items-end justify-between gap-1 overflow-x-auto pb-1">
      {items.map((item) => (
        <div
          key={item.label}
          className="flex min-w-[2.25rem] flex-1 flex-col items-center gap-1"
        >
          <span className="text-[10px] font-medium tabular-nums text-[#6b7280]">
            {item.count.toLocaleString("en-IN")}
          </span>
          <div
            className="w-full max-w-[40px] rounded-t-md bg-[#245dd8]"
            style={{ height: `${Math.max(10, (item.count / max) * 100)}%` }}
          />
          <span className="max-w-[3rem] truncate text-[9px] text-[#9ca3af]" title={item.label}>
            {item.label}
          </span>
        </div>
      ))}
    </div>
  );
}

function DistributionBars({ items }: { items: DistributionItem[] }) {
  if (!items.length) {
    return <p className="text-sm text-[#9ca3af]">No records for the selected filters.</p>;
  }
  const max = Math.max(...items.map((i) => i.count), 1);
  return (
    <ul className="space-y-3">
      {items.map((item) => (
        <li key={item.key}>
          <div className="mb-1 flex items-center justify-between text-[12px]">
            <span className="font-medium text-[#374151]">{item.label}</span>
            <span className="tabular-nums text-[#6b7280]">
              {item.count.toLocaleString("en-IN")}
              {item.share_pct != null ? ` · ${item.share_pct}%` : ""}
            </span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-[#eef2f7]">
            <div
              className="h-full rounded-full bg-[#245dd8]"
              style={{ width: `${Math.max(4, (item.count / max) * 100)}%` }}
            />
          </div>
        </li>
      ))}
    </ul>
  );
}

function formatAyLabel(label: string) {
  return label.replace(/-/g, "–");
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
          "w-full min-w-[8.75rem] cursor-pointer appearance-none truncate rounded-md border py-1.5 pr-8 text-xs outline-none transition-colors",
          leadingIcon ? "pl-8" : "pl-3",
          active
            ? "border-[#245dd8] bg-[#eef4ff] font-medium text-[#245dd8]"
            : "border-[#e5e7eb] bg-white text-[#374151]",
          disabled && "cursor-not-allowed opacity-60",
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

export function StudentStatisticsDashboard() {
  const [academicYear, setAcademicYear] = useState("");
  const [programmeCode, setProgrammeCode] = useState("");
  const [studyYear, setStudyYear] = useState("");

  const queryParams = useMemo(
    () => ({
      ...(academicYear ? { academic_year_label: academicYear } : {}),
      ...(programmeCode ? { programme_code: programmeCode } : {}),
      ...(studyYear ? { study_year: studyYear } : {}),
    }),
    [academicYear, programmeCode, studyYear],
  );

  const { data, isLoading, isError, error, refetch, isFetching } =
    useStudentStatisticsOverview(queryParams);

  const yearsQ = useQuery({
    queryKey: ["college-admin", "academic-years", "student-stats"],
    queryFn: fetchAcademicYears,
  });
  const programmesQ = useQuery({
    queryKey: ["college-admin", "programmes", "student-stats"],
    queryFn: fetchProgrammes,
  });

  const academicYearOptions = useMemo(() => {
    const labels = new Set<string>();
    for (const y of yearsQ.data ?? []) {
      if (y.label?.trim()) {
        labels.add(y.label.trim());
      }
    }
    const fromStats =
      data?.filters.academic_year_label?.trim() ||
      data?.academic_term.academic_year_label?.trim();
    if (fromStats) {
      labels.add(fromStats);
    }
    return Array.from(labels).sort((a, b) => b.localeCompare(a));
  }, [yearsQ.data, data?.filters.academic_year_label, data?.academic_term.academic_year_label]);

  const defaultAcademicYear = useMemo(() => {
    const current = (yearsQ.data ?? []).find((y) => y.is_current)?.label?.trim();
    if (current) return current;
    return (
      data?.filters.academic_year_label?.trim() ||
      data?.academic_term.academic_year_label?.trim() ||
      academicYearOptions[0] ||
      ""
    );
  }, [yearsQ.data, data, academicYearOptions]);

  useEffect(() => {
    if (academicYear || !defaultAcademicYear) return;
    setAcademicYear(defaultAcademicYear);
  }, [academicYear, defaultAcademicYear]);

  const selectedAcademicYear = useMemo(() => {
    if (academicYear) return academicYear;
    if (defaultAcademicYear) return defaultAcademicYear;
    return academicYearOptions[0] ?? "";
  }, [academicYear, academicYearOptions, defaultAcademicYear]);

  const handleExport = useCallback(() => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `student-statistics-${new Date(data.generated_at).toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data]);

  const deptChart = useMemo(
    () =>
      (data?.enrolment_by_department ?? []).map((d) => ({
        label: d.department_code,
        count: d.student_count,
      })),
    [data?.enrolment_by_department],
  );

  const kpis = data?.kpis;

  const totalEnrolledHint = useMemo(() => {
    if (kpis?.total_enrolled_change_pct == null) return undefined;
    const ref = kpis.total_enrolled_change_reference_year;
    const sign = kpis.total_enrolled_change_pct >= 0 ? "+" : "";
    return `${sign}${kpis.total_enrolled_change_pct}% vs ${ref ?? "prior year"}`;
  }, [kpis]);

  const admissionsHint = useMemo(() => {
    if (kpis?.new_admissions_intake_fill_pct != null) {
      return `${kpis.new_admissions_intake_fill_pct}% of sanctioned intake`;
    }
    if (kpis?.new_admissions_intake_sanctioned) {
      return `${kpis.new_admissions_intake_sanctioned} sanctioned intake`;
    }
    return "Confirmed admissions this academic year";
  }, [kpis]);

  const hostelHint = useMemo(() => {
    if (kpis?.hostel_residents_pct_of_enrolled != null) {
      return `${kpis.hostel_residents_pct_of_enrolled}% of enrolled students`;
    }
    return "Active hostel allocations";
  }, [kpis]);

  const discontinuedHint = useMemo(() => {
    if (kpis?.discontinued_pct_of_enrolled != null) {
      return `${kpis.discontinued_pct_of_enrolled}% of enrolled`;
    }
    return "Withdrawn this academic year";
  }, [kpis]);

  return (
    <div className="space-y-5" data-figma-frame="65:618">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            Student statistics
          </h2>
          <p className="mt-1 max-w-2xl text-[14px] leading-relaxed text-[#6b7280]">
            Enrolment, distribution and status across programmes and departments
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap items-center gap-2">
          <Button
            type="button"
            className="h-9 gap-1.5 border border-[#245dd8] bg-[#245dd8] text-xs font-medium text-white hover:bg-[#1f4fb8]"
            onClick={handleExport}
            disabled={isLoading || !data}
          >
            <CollegeAdminDownload className="size-3.5" />
            Export
          </Button>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <FilterSelect
          value={selectedAcademicYear || "__placeholder__"}
          onChange={setAcademicYear}
          active={Boolean(selectedAcademicYear)}
          aria-label="Academic year"
          className="min-w-[9.5rem]"
          leadingIcon={<CalendarIcon className="size-3.5" />}
          disabled={yearsQ.isLoading && academicYearOptions.length === 0}
        >
          {selectedAcademicYear || academicYearOptions.length > 0 ? null : (
            <option value="__placeholder__" disabled>
              {yearsQ.isLoading ? "Loading…" : "Academic year"}
            </option>
          )}
          {academicYearOptions.map((label) => (
            <option key={label} value={label}>
              {formatAyLabel(label)}
            </option>
          ))}
          {selectedAcademicYear && !academicYearOptions.includes(selectedAcademicYear) ? (
            <option value={selectedAcademicYear}>
              {formatAyLabel(selectedAcademicYear)}
            </option>
          ) : null}
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
          value={studyYear}
          onChange={setStudyYear}
          active={Boolean(studyYear)}
          aria-label="Study year"
          className="min-w-[8.5rem]"
          leadingIcon={<FilterIcon className="size-3.5" />}
        >
          {STUDY_YEAR_OPTIONS.map((opt) => (
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
                label="Total enrolled"
                value={kpis?.total_enrolled.toLocaleString("en-IN") ?? 0}
                hint={totalEnrolledHint}
                hintTone={
                  kpis?.total_enrolled_change_pct != null && kpis.total_enrolled_change_pct >= 0
                    ? "success"
                    : "muted"
                }
                kpiKey="total_enrolled"
                index={0}
              />
              <CollegeAdminDashboardKpiCard
                label="New admissions"
                value={kpis?.new_admissions.toLocaleString("en-IN") ?? 0}
                hint={admissionsHint}
                kpiKey="new_admissions"
                index={1}
              />
              <CollegeAdminDashboardKpiCard
                label="Hostel residents"
                value={kpis?.hostel_residents.toLocaleString("en-IN") ?? 0}
                hint={hostelHint}
                kpiKey="hostel_residents"
                index={2}
              />
              <CollegeAdminDashboardKpiCard
                label="Discontinued"
                value={kpis?.discontinued.toLocaleString("en-IN") ?? 0}
                hint={discontinuedHint}
                hintTone="warning"
                kpiKey="discontinued"
                index={3}
              />
            </CollegeAdminKpiGrid>

            <div className="grid gap-4 xl:grid-cols-3">
              <div className="space-y-4 xl:col-span-2">
                <Panel
                  title="Enrolment by department"
                  actionHref="/college-admin/students/all-students-list"
                  actionLabel="View all students →"
                >
                  <DepartmentBarChart items={deptChart} />
                </Panel>

                <Panel
                  title="Enrolment by programme and year"
                  actionHref="/college-admin/students/student-administration-dashboard"
                  actionLabel="Detailed report →"
                >
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[28rem] text-left text-[12px]">
                      <thead>
                        <tr className="border-b border-[#e8ecf2] text-[#6b7280]">
                          <th className="pb-2 pr-3 font-medium">Programme</th>
                          <th className="pb-2 px-2 text-right font-medium">Year 1</th>
                          <th className="pb-2 px-2 text-right font-medium">Year 2</th>
                          <th className="pb-2 px-2 text-right font-medium">Year 3</th>
                          <th className="pb-2 px-2 text-right font-medium">Year 4</th>
                          <th className="pb-2 pl-2 text-right font-medium">Total</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.programme_year_matrix.map((row) => (
                          <tr
                            key={row.group_key}
                            className="border-b border-[#f1f5f9] text-[#111827]"
                          >
                            <td className="py-2.5 pr-3 font-medium">{row.label}</td>
                            <td className="px-2 py-2.5 text-right tabular-nums">{row.year_1}</td>
                            <td className="px-2 py-2.5 text-right tabular-nums">{row.year_2}</td>
                            <td className="px-2 py-2.5 text-right tabular-nums">{row.year_3}</td>
                            <td className="px-2 py-2.5 text-right tabular-nums">{row.year_4}</td>
                            <td className="py-2.5 pl-2 text-right font-semibold tabular-nums">
                              {row.total}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <div className="mt-3 flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] pt-3 text-[11px] text-[#6b7280]">
                    <span>
                      {data.programme_matrix_group_count} programme groups ·{" "}
                      {data.programme_matrix_student_total.toLocaleString("en-IN")} students
                    </span>
                    <button
                      type="button"
                      className="font-medium text-[#245dd8] hover:underline"
                      onClick={handleExport}
                    >
                      Export table →
                    </button>
                  </div>
                </Panel>
              </div>

              <div className="space-y-4">
                <Panel
                  title="Gender distribution"
                  actionHref="/college-admin/students/admissions-list"
                  actionLabel="Report →"
                >
                  <DistributionBars items={data.gender_distribution} />
                </Panel>

                <Panel
                  title="Admission category"
                  actionHref="/college-admin/students/admissions-list"
                  actionLabel="Report →"
                >
                  <DistributionBars items={data.admission_category} />
                </Panel>

                <Panel
                  title="Student status"
                  actionHref="/college-admin/students/student-profile-management"
                  actionLabel="Status management →"
                >
                  <ul className="divide-y divide-[#f1f5f9]">
                    {data.student_status.map((row) => (
                      <li key={row.status_key} className="py-3 first:pt-0">
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <p className="text-[13px] font-semibold text-[#111827]">{row.label}</p>
                            <p className="text-[11px] text-[#9ca3af]">{row.description}</p>
                          </div>
                          <span className="shrink-0 text-[13px] font-semibold tabular-nums text-[#111827]">
                            {row.count.toLocaleString("en-IN")}
                          </span>
                        </div>
                      </li>
                    ))}
                  </ul>
                </Panel>
              </div>
            </div>

            <footer className="flex flex-wrap items-center justify-between gap-2 border-t border-[#e8ecf2] pt-4 text-[11px] text-[#9ca3af]">
              <span>
                Live institutional data · Student, hostel and admission records · All times IST
              </span>
            </footer>
          </>
        ) : (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard label="Total enrolled" value="—" />
          </div>
        )}
      </QueryState>
    </div>
  );
}