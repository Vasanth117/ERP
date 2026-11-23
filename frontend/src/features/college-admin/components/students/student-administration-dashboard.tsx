"use client";
import { CollegeAdminPlusActionLabel } from "@/features/college-admin/components/ui/college-admin-plus-action";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { CalendarIcon } from "@/components/icons/erp/generated/calendar";
import { FilterIcon } from "@/components/icons/erp/generated/filter";
import { TriangleAlertIcon } from "@/components/icons/erp/generated/triangle-alert";
import { Button } from "@/components/ui/button";
import { LayoutGridIcon } from "@/components/icons/erp/generated/layout-grid";
import {
  CollegeAdminDownload,
  getCollegeAdminErpIcon,
  resolveCollegeAdminIconSlug,
} from "@/features/college-admin/components/layout/college-admin-erp-icons";
import {
  CollegeAdminKpiGrid,
  CollegeAdminUserDashboardKpiCard,
} from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useStudentAdministrationDashboardPage } from "@/features/college-admin/hooks/use-student-administration-dashboard";
import type {
  StudentAdminDocumentAlert,
  StudentAdminWeeklySeriesPoint,
  StudentAdminWorkQueueItem,
} from "@/features/college-admin/types/student-administration-dashboard";
import { cn } from "@/lib/utils";

function FilterSelect({
  icon,
  label,
  value,
  onChange,
  options,
  className,
}: {
  icon?: React.ReactNode;
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
  className?: string;
}) {
  return (
    <div className={cn("relative", className)}>
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

function AdmissionsWeeklyChart({
  points,
  currentLabel,
  previousLabel,
}: {
  points: StudentAdminWeeklySeriesPoint[];
  currentLabel: string;
  previousLabel: string;
}) {
  if (!points.length) {
    return <p className="text-sm text-[#9ca3af]">No weekly admission data for the selected year.</p>;
  }
  const values = points.flatMap((p) => [p.current_year_count, p.previous_year_count]);
  const peak = Math.max(...values, 0);
  const max = Math.max(peak, 1);
  const allZero = peak === 0;
  const w = 520;
  const h = 168;
  const pad = 24;
  const toX = (i: number) => pad + (i * (w - 2 * pad)) / Math.max(points.length - 1, 1);
  const toY = (v: number) => h - pad - (v / max) * (h - 2 * pad);
  const currentLine = points.map((p, i) => `${toX(i)},${toY(p.current_year_count)}`).join(" ");
  const prevLine = points.map((p, i) => `${toX(i)},${toY(p.previous_year_count)}`).join(" ");

  return (
    <div>
      {allZero ? (
        <p className="mb-2 text-[12px] text-[#9ca3af]">No confirmed admissions in the selected weeks yet.</p>
      ) : null}
      <svg viewBox={`0 0 ${w} ${h}`} className="h-44 w-full" role="img" aria-label="Weekly admissions comparison">
        {[0, 0.5, 1].map((tick) => {
          const y = h - pad - tick * (h - 2 * pad);
          return (
            <line key={tick} x1={pad} y1={y} x2={w - pad} y2={y} stroke="#f1f5f9" strokeDasharray={tick === 0 ? undefined : "4 4"} />
          );
        })}
        <line x1={pad} y1={h - pad} x2={w - pad} y2={h - pad} stroke="#e8ecf2" />
        {!allZero ? (
          <>
            <polyline fill="none" stroke="#245dd8" strokeWidth="2.5" points={currentLine} />
            <polyline
              fill="none"
              stroke="#93c5fd"
              strokeWidth="2"
              strokeDasharray="6 4"
              points={prevLine}
            />
            {points.map((p, i) => (
              <g key={p.week_label}>
                <circle cx={toX(i)} cy={toY(p.current_year_count)} r="3.5" fill="#245dd8" />
                <circle cx={toX(i)} cy={toY(p.previous_year_count)} r="3" fill="#93c5fd" />
              </g>
            ))}
          </>
        ) : (
          <line x1={pad} y1={h - pad} x2={w - pad} y2={h - pad} stroke="#cbd5e1" strokeWidth="1.5" strokeDasharray="5 5" />
        )}
      </svg>
      <div className="mt-1 flex justify-between gap-1 text-[9px] text-[#9ca3af]">
        {points.map((p) => (
          <span key={p.week_label} className="max-w-[3rem] truncate">
            {p.week_label.replace("Week ", "W")}
          </span>
        ))}
      </div>
      <div className="mt-2 flex flex-wrap gap-4 text-[11px] text-[#6b7280]">
        <span className="flex items-center gap-1.5">
          <span className="h-0.5 w-4 bg-[#245dd8]" />
          {currentLabel}
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-0.5 w-4 border-t-2 border-dashed border-[#93c5fd]" />
          {previousLabel}
        </span>
      </div>
    </div>
  );
}

function DocumentAlertBanner({ alert }: { alert: StudentAdminDocumentAlert }) {
  return (
    <div className="flex flex-col gap-2 rounded-xl border border-[#fde68a] bg-[#fffbeb] p-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex gap-3">
        <TriangleAlertIcon className="mt-0.5 size-5 shrink-0 text-[#d97706]" aria-hidden />
        <div>
          <p className="text-[13px] font-semibold text-[#92400e]">{alert.title}</p>
          <p className="mt-1 text-[12px] leading-relaxed text-[#a16207]">{alert.description}</p>
        </div>
      </div>
      <Link href={alert.continue_href} className="shrink-0 text-[12px] font-medium text-[#245dd8] hover:underline">
        {alert.continue_label}
      </Link>
    </div>
  );
}

function WorkQueueRow({ item }: { item: StudentAdminWorkQueueItem }) {
  const slug = resolveCollegeAdminIconSlug(item.icon_slug);
  const Icon = getCollegeAdminErpIcon(slug) ?? LayoutGridIcon;
  return (
    <li className="flex items-center justify-between gap-3 border-b border-[#f1f5f9] py-3.5 last:border-0">
      <div className="flex min-w-0 items-center gap-3">
        <Icon className="size-[18px] shrink-0 text-[#9ca3af]" aria-hidden strokeWidth={1.75} />
        <div className="min-w-0">
          <p className="text-[13px] font-medium text-[#111827]">{item.title}</p>
          <p className="text-[12px] text-[#6b7280]">
            {item.count.toLocaleString("en-IN")} {item.subtitle.toLowerCase()}
          </p>
        </div>
      </div>
      <Link href={item.href} className="shrink-0 text-[12px] font-medium text-[#245dd8] hover:underline">
        {item.action_label}
      </Link>
    </li>
  );
}

function formatAyLabel(label: string) {
  return label.replace(/-/g, "–");
}


export function StudentAdministrationDashboard() {
  const [academicYear, setAcademicYear] = useState("");
  const [programme, setProgramme] = useState("");
  const [studyYear, setStudyYear] = useState("");

  const queryParams = {
    academic_year_code: academicYear || undefined,
    programme_code: programme || undefined,
    study_year: studyYear || undefined,
  };

  const { data, isLoading, isError, error, refetch } = useStudentAdministrationDashboardPage(queryParams);

  useEffect(() => {
    if (data?.selected_academic_year && !academicYear) {
      setAcademicYear(data.selected_academic_year);
    }
  }, [data?.selected_academic_year, academicYear]);

  const handleExport = useCallback(() => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `student-administration-${new Date(data.generated_at).toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data]);

  return (
    <div className="space-y-5" data-figma-frame="69:145600">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-wrap items-center gap-2">
          <FilterSelect
            icon={<CalendarIcon className="size-3.5" aria-hidden />}
            label={data?.academic_year_filter_label ?? "Academic year"}
            value={academicYear}
            onChange={setAcademicYear}
            options={
              data?.academic_year_options?.map((o) => ({
                value: o.value,
                label: formatAyLabel(o.label),
              })) ?? []
            }
          />
          <FilterSelect
            icon={<FilterIcon className="size-3.5" aria-hidden />}
            label={data?.programme_filter_label ?? "Programme"}
            value={programme}
            onChange={setProgramme}
            options={data?.programme_options ?? [{ value: "", label: "All programmes" }]}
          />
          <FilterSelect
            icon={<FilterIcon className="size-3.5" aria-hidden />}
            label={data?.study_year_filter_label ?? "Study year"}
            value={studyYear}
            onChange={setStudyYear}
            options={data?.study_year_options ?? [{ value: "", label: "All years" }]}
          />
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <Button
            type="button"
            variant="outline"
            className="h-9 gap-1.5 border-[#dce3ec] text-xs font-medium text-[#374151]"
            onClick={handleExport}
            disabled={isLoading || !data}
          >
            <CollegeAdminDownload className="size-3.5" />
            {data?.export_label ?? "Export"}
          </Button>
          <Link
            href={data?.new_admission_href ?? "/college-admin/students/new-student-registration"}
            className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
          >
            <CollegeAdminPlusActionLabel iconClassName="size-3.5" label={data?.new_admission_label ?? "New admission" } />
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

            {data.document_alert ? <DocumentAlertBanner alert={data.document_alert} /> : null}

            <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_360px]">
              <div className="space-y-5">
                <section className="rounded-xl border border-[#e8ecf2] bg-white p-4 shadow-[0_1px_2px_rgba(15,23,42,0.04)] sm:p-5">
                  <h3 className="mb-4 text-[14px] font-semibold text-[#111827]">{data.admissions_chart_title}</h3>
                  <AdmissionsWeeklyChart
                    points={data.admissions_weekly_series}
                    currentLabel={data.admissions_chart_current_label}
                    previousLabel={data.admissions_chart_previous_label}
                  />
                </section>

                <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                  <div className="flex items-center justify-between border-b border-[#f1f5f9] px-5 py-3.5">
                    <h3 className="text-[14px] font-semibold text-[#111827]">{data.recent_admissions_title}</h3>
                    <Link
                      href={data.recent_admissions_view_all_href}
                      className="text-[12px] font-medium text-[#245dd8] hover:underline"
                    >
                      All admissions →
                    </Link>
                  </div>
                  {data.recent_admissions_rows.length ? (
                    <div className="overflow-x-auto">
                      <table className="w-full min-w-[36rem] text-left text-[13px]">
                        <thead>
                          <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                            {data.recent_admissions_headers.map((header, index) => (
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
                          {data.recent_admissions_rows.map((row) => (
                            <tr key={row.admission_id} className="hover:bg-[#f9fafb]">
                              <td className="px-5 py-3 font-medium text-[#111827]">
                                <Link href={row.detail_href} className="hover:text-[#245dd8]">
                                  {row.student_name}
                                </Link>
                              </td>
                              <td className="py-3 pr-3 text-[#374151]">{row.programme_label}</td>
                              <td className="py-3 pr-3 text-[#374151]">{row.quota_label}</td>
                              <td className="py-3 pr-3 tabular-nums text-[#374151]">{row.admitted_label}</td>
                              <td className="py-3 pr-5">
                                <StatusPill label={row.documents_status_label} tone={row.documents_status_tone} />
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="px-5 py-10 text-center text-sm text-[#9ca3af]">No recent admissions in scope.</p>
                  )}
                  <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
                    <span>{data.recent_admissions_footer_label}</span>
                    <Link
                      href={data.recent_admissions_view_all_href}
                      className="font-medium text-[#245dd8] hover:underline"
                    >
                      {data.recent_admissions_view_all_label}
                    </Link>
                  </div>
                </section>
              </div>

              <div className="space-y-5">
                <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                  <h3 className="mb-4 text-[14px] font-semibold text-[#111827]">{data.enrollment_by_year_title}</h3>
                  <ul className="space-y-3.5">
                    {data.enrollment_year_bars.map((bar) => (
                      <li key={bar.year_key}>
                        <div className="mb-1 flex items-center justify-between text-[12px]">
                          <span className="font-medium text-[#374151]">{bar.year_label}</span>
                          <span className="tabular-nums text-[#6b7280]">
                            {bar.student_count.toLocaleString("en-IN")}
                          </span>
                        </div>
                        <div className="h-2 overflow-hidden rounded-full bg-[#eef2f7]">
                          <div
                            className="h-full rounded-full bg-[#245dd8]"
                            style={{
                              width: `${bar.student_count > 0 ? Math.max(4, bar.share_percent) : 0}%`,
                            }}
                          />
                        </div>
                      </li>
                    ))}
                  </ul>
                </section>

                <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                  <h3 className="mb-1 text-[14px] font-semibold text-[#111827]">{data.work_queue_title}</h3>
                  <ul>{data.work_queue_items.map((item) => <WorkQueueRow key={item.key} item={item} />)}</ul>
                </section>

                <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                  <h3 className="mb-4 text-[14px] font-semibold text-[#111827]">{data.student_status_title}</h3>
                  <ul className="space-y-3">
                    {data.student_status_items.map((item) => (
                      <li key={item.status_key} className="flex items-center justify-between text-[13px]">
                        <span className="text-[#374151]">{item.status_label}</span>
                        <span className="font-semibold tabular-nums text-[#111827]">
                          {item.student_count.toLocaleString("en-IN")}
                        </span>
                      </li>
                    ))}
                  </ul>
                </section>
              </div>
            </div>

          </>
        ) : null}
      </QueryState>
    </div>
  );
}