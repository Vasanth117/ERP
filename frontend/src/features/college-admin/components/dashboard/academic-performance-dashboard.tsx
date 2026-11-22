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
import { fetchAcademicTerms, fetchAcademicYears, fetchProgrammes } from "@/features/college-admin/api/academics";
import { CollegeAdminDashboardKpiCard, CollegeAdminKpiGrid } from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useAcademicPerformanceOverview } from "@/features/college-admin/hooks/use-academic-performance";
import { cn } from "@/lib/utils";

const STUDY_YEAR_OPTIONS = [
  { value: "", label: "All years" },
  { value: "1", label: "Year 1" },
  { value: "2", label: "Year 2" },
  { value: "3", label: "Year 3" },
  { value: "4", label: "Year 4" },
];


function TrendPill({ trendKey, label }: { trendKey: string; label: string }) {
  const tone =
    trendKey === "improving"
      ? "bg-[#ecfdf5] text-[#047857]"
      : trendKey === "declining"
        ? "bg-[#fef2f2] text-[#b91c1c]"
        : "bg-[#fff7ed] text-[#c2410c]";
  const dot =
    trendKey === "improving" ? "bg-[#10b981]" : trendKey === "declining" ? "bg-[#ef4444]" : "bg-[#f97316]";
  return (
    <span className={cn("inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium", tone)}>
      <span className={cn("size-1.5 rounded-full", dot)} />
      {label}
    </span>
  );
}


function PassTrendChart({
  points,
}: {
  points: { label: string; college: number | null; benchmark: number | null }[];
}) {
  if (!points.length) {
    return <p className="text-sm text-[#9ca3af]">No examination sessions with published results yet.</p>;
  }
  const values = points.flatMap((p) => [p.college, p.benchmark].filter((v): v is number => v != null));
  const min = Math.min(...values, 70);
  const max = Math.max(...values, 100);
  const span = Math.max(max - min, 10);
  const w = 480;
  const h = 160;
  const pad = 24;
  const toX = (i: number) => pad + (i * (w - 2 * pad)) / Math.max(points.length - 1, 1);
  const toY = (v: number) => h - pad - ((v - min) / span) * (h - 2 * pad);
  const collegeLine = points
    .map((p, i) => (p.college != null ? `${toX(i)},${toY(p.college)}` : null))
    .filter(Boolean)
    .join(" ");
  const benchLine = points
    .map((p, i) => (p.benchmark != null ? `${toX(i)},${toY(p.benchmark)}` : null))
    .filter(Boolean)
    .join(" ");

  return (
    <div>
      <svg viewBox={`0 0 ${w} ${h}`} className="h-40 w-full">
        <line x1={pad} y1={h - pad} x2={w - pad} y2={h - pad} stroke="#e8ecf2" />
        {collegeLine ? (
          <polyline fill="none" stroke="#245dd8" strokeWidth="2.5" points={collegeLine} />
        ) : null}
        {benchLine ? (
          <polyline
            fill="none"
            stroke="#93c5fd"
            strokeWidth="2"
            strokeDasharray="6 4"
            points={benchLine}
          />
        ) : null}
      </svg>
      <div className="mt-1 flex justify-between text-[9px] text-[#9ca3af]">
        {points.map((p) => (
          <span key={p.label} className="max-w-[3.5rem] truncate">
            {p.label}
          </span>
        ))}
      </div>
      <div className="mt-2 flex gap-4 text-[11px] text-[#6b7280]">
        <span className="flex items-center gap-1.5">
          <span className="h-0.5 w-4 bg-[#245dd8]" /> College pass rate
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-0.5 w-4 border-t-2 border-dashed border-[#93c5fd]" /> University average
        </span>
      </div>
    </div>
  );
}

function StudyYearBars({
  items,
}: {
  items: { label: string; rate: number | null }[];
}) {
  const max = Math.max(...items.map((i) => i.rate ?? 0), 1);
  if (!items.length) return <p className="text-sm text-[#9ca3af]">No pass rate data by year of study.</p>;
  return (
    <div className="flex h-40 items-end justify-between gap-2">
      {items.map((item) => (
        <div key={item.label} className="flex flex-1 flex-col items-center gap-1">
          <span className="text-[10px] tabular-nums text-[#6b7280]">
            {item.rate != null ? `${item.rate}%` : "—"}
          </span>
          <div
            className="w-full max-w-[48px] rounded-t-md bg-[#245dd8]"
            style={{ height: `${item.rate != null ? Math.max(8, (item.rate / max) * 100) : 4}%` }}
          />
          <span className="text-[9px] text-[#9ca3af]">{item.label}</span>
        </div>
      ))}
    </div>
  );
}

function GradeBars({ items }: { items: { label: string; count: number; share_pct: number | null }[] }) {
  if (!items.length) return <p className="text-sm text-[#9ca3af]">No graded results for the selected term.</p>;
  const max = Math.max(...items.map((i) => i.count), 1);
  return (
    <ul className="space-y-2.5">
      {items.map((item) => (
        <li key={item.label}>
          <div className="mb-1 flex justify-between text-[12px]">
            <span className="text-[#374151]">{item.label}</span>
            <span className="tabular-nums text-[#6b7280]">
              {item.share_pct != null ? `${item.share_pct}%` : item.count}
            </span>
          </div>
          <div className="h-2 rounded-full bg-[#eef2f7]">
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

function RiskCount({ riskKey, count }: { riskKey: string; count: number }) {
  const style =
    riskKey === "arrears_3_plus"
      ? "bg-[#fef2f2] text-[#b91c1c]"
      : riskKey === "cgpa_below_5"
        ? "bg-[#fff7ed] text-[#c2410c]"
        : "bg-[#fff7ed] text-[#c2410c]";
  return (
    <span className={cn("rounded-full px-2.5 py-0.5 text-[12px] font-semibold tabular-nums", style)}>{count}</span>
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

export function AcademicPerformanceDashboard() {
  const [academicYear, setAcademicYear] = useState("");
  const [semesterLabel, setSemesterLabel] = useState("");
  const [programmeCode, setProgrammeCode] = useState("");
  const [studyYear, setStudyYear] = useState("");

  const yearsQ = useQuery({ queryKey: ["ca", "years", "academic"], queryFn: fetchAcademicYears });
  const termsQ = useQuery({ queryKey: ["ca", "terms", "academic"], queryFn: () => fetchAcademicTerms() });
  const programmesQ = useQuery({ queryKey: ["ca", "programmes", "academic"], queryFn: fetchProgrammes });

  const queryParams = useMemo(
    () => ({
      ...(academicYear ? { academic_year_label: academicYear } : {}),
      ...(semesterLabel ? { semester_label: semesterLabel } : {}),
      ...(programmeCode ? { programme_code: programmeCode } : {}),
      ...(studyYear ? { study_year: studyYear } : {}),
    }),
    [academicYear, semesterLabel, programmeCode, studyYear],
  );

  const { data, isLoading, isError, error, refetch, isFetching } = useAcademicPerformanceOverview(queryParams);

  const defaultYear = useMemo(
    () => yearsQ.data?.find((y) => y.is_current)?.label ?? data?.filters.academic_year_label ?? "",
    [yearsQ.data, data],
  );
  const defaultSemester = useMemo(
    () => termsQ.data?.find((t) => t.is_current)?.label ?? data?.filters.semester_label ?? "",
    [termsQ.data, data],
  );

  useEffect(() => {
    if (!academicYear && defaultYear) setAcademicYear(defaultYear);
  }, [academicYear, defaultYear]);
  useEffect(() => {
    if (!semesterLabel && defaultSemester) setSemesterLabel(defaultSemester);
  }, [semesterLabel, defaultSemester]);

  const semesterOptions = useMemo(() => {
    const s = new Set<string>();
    termsQ.data?.forEach((t) => t.label && s.add(t.label));
    if (defaultSemester) s.add(defaultSemester);
    if (semesterLabel) s.add(semesterLabel);
    return Array.from(s);
  }, [termsQ.data, defaultSemester, semesterLabel]);

  const semesterValue = semesterLabel || defaultSemester || semesterOptions[0] || "";
  const resultsFilterLabel =
    data?.results_display_label ??
    (semesterValue && academicYear
      ? `${semesterValue} semester ${academicYear.split("-")[0]} results`
      : "Latest results");

  const handleExport = useCallback(() => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `academic-performance-${new Date(data.generated_at).toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data]);

  const kpis = data?.kpis;
  const trendPoints = useMemo(
    () =>
      (data?.pass_rate_trend ?? []).map((p) => ({
        label: p.label,
        college: p.college_pass_rate_pct,
        benchmark: p.university_benchmark_pct,
      })),
    [data?.pass_rate_trend],
  );
  const studyBars = useMemo(
    () =>
      (data?.pass_rate_by_study_year ?? []).map((b) => ({
        label: b.label,
        rate: b.pass_rate_pct,
      })),
    [data?.pass_rate_by_study_year],
  );

  const passChangeHint = useMemo(() => {
    if (kpis?.overall_pass_rate_change_pts == null) return "Compared to previous published semester";
    const sign = kpis.overall_pass_rate_change_pts >= 0 ? "+" : "";
    const ref = kpis.overall_pass_rate_reference_label ?? "previous semester";
    return `${sign}${kpis.overall_pass_rate_change_pts} pts vs ${ref}`;
  }, [kpis]);

  return (
    <div className="space-y-5" data-figma-frame="66:1973">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold text-[#111827]">Academic performance analytics</h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">
            Results, grades and at-risk students from the latest published examinations
          </p>
        </div>
        <div className="flex gap-2">
          <Button type="button" className="h-9 gap-1.5 bg-[#245dd8] text-xs text-white" onClick={handleExport} disabled={!data}>
            <CollegeAdminDownload className="size-3.5" />
            Export analysis
          </Button>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <FilterSelect
          value={semesterValue || "__ph__"}
          onChange={setSemesterLabel}
          active={Boolean(semesterValue)}
          aria-label="Results term"
          className="min-w-[13rem]"
          leadingIcon={<CalendarIcon className="size-3.5" />}
        >
          {!semesterValue ? <option value="__ph__">Results term</option> : null}
          {semesterOptions.map((l) => (
            <option key={l} value={l}>
              {l === semesterValue ? resultsFilterLabel : l}
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
        <FilterSelect
          value={studyYear}
          onChange={setStudyYear}
          active={Boolean(studyYear)}
          aria-label="Study year"
          className="min-w-[8rem]"
          leadingIcon={<FilterIcon className="size-3.5" />}
        >
          {STUDY_YEAR_OPTIONS.map((o) => (
            <option key={o.value || "all"} value={o.value}>
              {o.label}
            </option>
          ))}
        </FilterSelect>
      </div>

      <QueryState isLoading={isLoading || isFetching} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            <CollegeAdminKpiGrid>
              <CollegeAdminDashboardKpiCard
                label="Overall pass rate"
                value={kpis?.overall_pass_rate_pct != null ? `${kpis.overall_pass_rate_pct}%` : "—"}
                hint={passChangeHint}
                hintTone={
                  kpis?.overall_pass_rate_change_pts != null && kpis.overall_pass_rate_change_pts >= 0
                    ? "success"
                    : "muted"
                }
              />
              <CollegeAdminDashboardKpiCard
                label="Average CGPA"
                value={kpis?.average_cgpa ?? "—"}
                hint={
                  kpis?.average_cgpa_ug != null || kpis?.average_cgpa_pg != null
                    ? `UG ${kpis?.average_cgpa_ug ?? "—"} · PG ${kpis?.average_cgpa_pg ?? "—"}`
                    : "Published semester results"
                }
              />
              <CollegeAdminDashboardKpiCard
                label="First class with distinction"
                value={kpis?.first_class_distinction_pct != null ? `${kpis.first_class_distinction_pct}%` : "—"}
                hint={`${kpis?.first_class_distinction_student_count ?? 0} students`}
              />
              <CollegeAdminDashboardKpiCard
                label="Students with backlogs"
                value={kpis?.students_with_backlogs ?? 0}
                hint={`${kpis?.students_with_backlogs_pct ?? "—"}% · ${kpis?.students_with_three_plus_arrears ?? 0} with 3+ arrears`}
                hintTone="warning"
              />
            </CollegeAdminKpiGrid>

            <div className="grid gap-4 xl:grid-cols-3">
              <div className="space-y-4 xl:col-span-2">
                <Panel title="Pass rate trend by semester" actionHref="/college-admin/dashboard/academic-analytics" actionLabel="Result analysis →">
                  <PassTrendChart points={trendPoints} />
                </Panel>
                <Panel title="Pass rate by year of study" actionHref="/college-admin/academics" actionLabel="Detailed report →">
                  <StudyYearBars items={studyBars} />
                </Panel>
                <Panel title="Subjects with the lowest pass rate" actionHref="/college-admin/examinations" actionLabel="All subjects →">
                  <LowPassSubjectsTable data={data} onExport={handleExport} />
                </Panel>
              </div>
              <div className="space-y-4">
                <Panel title="Grade distribution">
                  <GradeBars
                    items={(data.grade_distribution ?? []).map((g) => ({
                      label: g.label,
                      count: g.count,
                      share_pct: g.share_pct,
                    }))}
                  />
                </Panel>
                <Panel title="Students at academic risk" actionHref="/college-admin/students/all-students-list" actionLabel="View all →">
                  <ul className="divide-y divide-[#f1f5f9]">
                    {data.academic_risk.map((r) => (
                      <li key={r.risk_key} className="flex items-center justify-between gap-2 py-3 first:pt-0">
                        <div>
                          <p className="text-[13px] font-semibold text-[#111827]">{r.label}</p>
                          {r.description ? <p className="text-[11px] text-[#9ca3af]">{r.description}</p> : null}
                        </div>
                        <RiskCount riskKey={r.risk_key} count={r.count} />
                      </li>
                    ))}
                  </ul>
                </Panel>
                <Panel title="Top performers" actionHref="/college-admin/examinations" actionLabel="Merit list →">
                  {data.top_performers.length ? (
                    <ul className="space-y-3">
                      {data.top_performers.map((p) => (
                        <li key={p.user_id} className="text-[13px]">
                          <p className="font-semibold text-[#111827]">{p.full_name}</p>
                          <p className="text-[12px] text-[#6b7280]">
                            {p.programme_label ?? "—"} · CGPA {p.cgpa.toFixed(2)}
                          </p>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm text-[#9ca3af]">No CGPA data for this term yet.</p>
                  )}
                </Panel>
              </div>
            </div>

            <footer className="flex flex-wrap justify-between gap-2 border-t border-[#e8ecf2] pt-4 text-[11px] text-[#9ca3af]">
              <span>Live institutional data · Examinations, grades and attendance · All times IST</span>
            </footer>
          </>
        ) : null}
      </QueryState>
    </div>
  );
}

function LowPassSubjectsTable({
  data,
  onExport,
}: {
  data: import("@/features/college-admin/types/academic-performance").AcademicPerformanceOverview;
  onExport: () => void;
}) {
  const rows = data.low_pass_subjects;
  if (!rows.length) {
    return <p className="text-sm text-[#9ca3af]">No subjects below {data.low_pass_subjects_below_pct}% for this term.</p>;
  }
  return (
    <>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[36rem] text-left text-[12px]">
          <thead>
            <tr className="border-b border-[#e8ecf2] text-[#6b7280]">
              <th className="pb-2 pr-2 font-medium">Subject</th>
              <th className="pb-2 px-2 font-medium">Department</th>
              <th className="pb-2 px-2 font-medium">Semester</th>
              <th className="pb-2 px-2 text-right font-medium">Appeared</th>
              <th className="pb-2 px-2 text-right font-medium">Pass %</th>
              <th className="pb-2 pl-2 font-medium">Trend</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.course_code} className="border-b border-[#f1f5f9]">
                <td className="py-2 pr-2 font-medium text-[#111827]">
                  {row.course_code}
                  {row.course_name && row.course_name !== row.course_code ? (
                    <span className="mt-0.5 block text-[11px] font-normal text-[#9ca3af]">{row.course_name}</span>
                  ) : null}
                </td>
                <td className="px-2 py-2">{row.department_code ?? row.department_name ?? "—"}</td>
                <td className="px-2 py-2">{row.semester_label ?? "—"}</td>
                <td className="px-2 py-2 text-right tabular-nums">{row.appeared_count}</td>
                <td className="px-2 py-2 text-right tabular-nums">
                  {row.pass_rate_pct != null ? `${row.pass_rate_pct}%` : "—"}
                </td>
                <td className="py-2 pl-2">
                  <TrendPill trendKey={row.trend_key} label={row.trend_label} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-3 flex justify-between border-t border-[#f1f5f9] pt-3 text-[11px] text-[#6b7280]">
        <span>Subjects below {data.low_pass_subjects_below_pct}% pass rate</span>
        <button type="button" className="font-medium text-[#245dd8] hover:underline" onClick={onExport}>
          Export list →
        </button>
      </div>
    </>
  );
}