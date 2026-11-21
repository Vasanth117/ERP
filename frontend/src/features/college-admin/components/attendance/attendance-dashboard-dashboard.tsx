"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { CalendarIcon } from "@/components/icons/erp/generated/calendar";
import { FilterIcon } from "@/components/icons/erp/generated/filter";
import { Button } from "@/components/ui/button";
import {
  CollegeAdminChevronRight,
  CollegeAdminDownload,
  getCollegeAdminErpIcon,
  resolveCollegeAdminIconSlug,
} from "@/features/college-admin/components/layout/college-admin-erp-icons";
import {
  CollegeAdminKpiGrid,
  CollegeAdminUserDashboardKpiCard,
} from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useAttendanceDashboardPage } from "@/features/college-admin/hooks/use-attendance-dashboard";
import type {
  AttendanceDashboardDepartmentRow,
  AttendanceDashboardTrendPoint,
} from "@/features/college-admin/types/attendance-dashboard";
import type { StudentAdminWorkQueueItem } from "@/features/college-admin/types/student-administration-dashboard";
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

function TrendPill({ row }: { row: AttendanceDashboardDepartmentRow }) {
  const tone =
    row.trend_tone === "success"
      ? "bg-[#ecfdf5] text-[#047857]"
      : row.trend_tone === "warning"
        ? "bg-[#fff7ed] text-[#c2410c]"
        : "bg-[#f3f4f6] text-[#6b7280]";
  return (
    <span className={cn("inline-flex rounded-full px-2.5 py-0.5 text-[11px] font-medium", tone)}>
      {row.trend_label}
    </span>
  );
}

function AttendanceTrendChart({ points }: { points: AttendanceDashboardTrendPoint[] }) {
  if (!points.length) {
    return <p className="text-sm text-[#9ca3af]">No attendance sessions in this range yet.</p>;
  }
  const values = points.map((p) => p.attendance_pct).filter((v): v is number => v != null);
  const min = Math.min(...values, 70);
  const max = Math.max(...values, 100);
  const span = Math.max(max - min, 8);
  const w = 640;
  const h = 160;
  const pad = 24;
  const toX = (i: number) => pad + (i * (w - 2 * pad)) / Math.max(points.length - 1, 1);
  const toY = (v: number) => h - pad - ((v - min) / span) * (h - 2 * pad);
  const line = points
    .map((p, i) => (p.attendance_pct != null ? `${toX(i)},${toY(p.attendance_pct)}` : null))
    .filter(Boolean)
    .join(" ");

  return (
    <div>
      <svg viewBox={`0 0 ${w} ${h}`} className="h-44 w-full" role="img" aria-label="Attendance trend">
        <line x1={pad} y1={h - pad} x2={w - pad} y2={h - pad} stroke="#e8ecf2" />
        {line ? <polyline fill="none" stroke="#245dd8" strokeWidth="2.5" points={line} /> : null}
      </svg>
      <div className="mt-1 flex justify-between gap-1 text-[9px] text-[#9ca3af]">
        {points.map((p) => (
          <span key={p.date_label} className="max-w-[2.5rem] truncate">
            {p.date_label}
          </span>
        ))}
      </div>
    </div>
  );
}

function AttentionRow({ item }: { item: StudentAdminWorkQueueItem }) {
  const slug = resolveCollegeAdminIconSlug(item.icon_slug);
  const Icon = getCollegeAdminErpIcon(slug);
  return (
    <li className="flex items-center justify-between gap-3 border-b border-[#f1f5f9] py-3.5 last:border-0">
      <div className="flex min-w-0 items-center gap-3">
        {Icon ? (
          <Icon className="size-[18px] shrink-0 text-[#9ca3af]" aria-hidden />
        ) : (
          <span className="size-[18px] shrink-0 rounded bg-[#f3f4f6]" aria-hidden />
        )}
        <div className="min-w-0">
          <p className="text-[13px] font-medium text-[#111827]">{item.title}</p>
          <p className="text-[12px] text-[#6b7280]">
            {item.count.toLocaleString("en-IN")} {item.subtitle}
          </p>
        </div>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <span
          className={cn(
            "inline-flex min-w-[1.5rem] items-center justify-center rounded-md px-1.5 py-0.5 text-[11px] font-semibold tabular-nums",
            item.key === "classes_not_marked" ? "bg-[#fef2f2] text-[#b91c1c]" : "bg-[#fff7ed] text-[#c2410c]",
          )}
        >
          {item.count.toLocaleString("en-IN")}
        </span>
        <Link href={item.href} className="text-[12px] font-medium text-[#245dd8] hover:underline">
          {item.action_label}
        </Link>
      </div>
    </li>
  );
}

export function AttendanceDashboardDashboard() {
  const [termKey, setTermKey] = useState("");
  const [departmentId, setDepartmentId] = useState("");

  const queryParams = {
    term_key: termKey || undefined,
    department_id: departmentId || undefined,
  };

  const { data, isLoading, isError, error, refetch } = useAttendanceDashboardPage(queryParams);

  useEffect(() => {
    if (data?.selected_term_key && !termKey) {
      setTermKey(data.selected_term_key);
    }
  }, [data?.selected_term_key, termKey]);

  const handleExport = useCallback(() => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `attendance-dashboard-${new Date(data.generated_at).toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data]);

  return (
    <div className="space-y-5" data-figma-frame="159:6844">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Attendance Dashboard"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">{data?.page_subtitle ?? "—"}</p>
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
            href={data?.open_reports_href ?? "/college-admin/attendance/attendance-reports"}
            className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
          >
            {data?.open_reports_label ?? "Open reports"}
            <CollegeAdminChevronRight className="size-3.5" aria-hidden />
          </Link>
        </div>
      </div>

      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-wrap items-center gap-2">
          <FilterSelect
            icon={<CalendarIcon className="size-3.5" aria-hidden />}
            label={data?.term_filter_label ?? "Academic term"}
            value={termKey}
            onChange={setTermKey}
            options={data?.term_options ?? []}
          />
          <FilterSelect
            icon={<FilterIcon className="size-3.5" aria-hidden />}
            label={data?.department_filter_label ?? "Department"}
            value={departmentId}
            onChange={setDepartmentId}
            options={data?.department_options ?? [{ value: "", label: "All departments" }]}
          />
        </div>
        <div className="flex flex-wrap items-center gap-3 text-[12px] text-[#6b7280]">
          <span className="inline-flex items-center gap-1.5 rounded-full border border-[#e8ecf2] bg-white px-2.5 py-1">
            <span className="size-1.5 rounded-full bg-[#245dd8]" />
            {data?.scope_indicator_label ?? "College scope"}
          </span>
          <span className="tabular-nums">{data?.updated_at_label ?? "—"}</span>
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

            <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_360px]">
              <div className="space-y-5">
                <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                  <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                    <h3 className="text-[14px] font-semibold text-[#111827]">{data.department_table_title}</h3>
                  </div>
                  {data.department_rows.length ? (
                    <div className="overflow-x-auto">
                      <table className="w-full min-w-[40rem] text-left text-[13px]">
                        <thead>
                          <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                            {data.department_table_headers.map((header, index) => (
                              <th
                                key={header}
                                className={cn(
                                  "pb-3 font-medium",
                                  index === 0 ? "px-5" : "pr-3 text-right",
                                  index === data.department_table_headers.length - 1 && "text-left",
                                )}
                              >
                                {header}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-[#f1f5f9]">
                          {data.department_rows.map((row) => (
                            <tr key={row.department_id} className="hover:bg-[#f9fafb]">
                              <td className="px-5 py-3 font-medium text-[#111827]">{row.department_name}</td>
                              <td className="py-3 pr-3 text-right tabular-nums text-[#374151]">
                                {row.student_count.toLocaleString("en-IN")}
                              </td>
                              <td className="py-3 pr-3 text-right tabular-nums text-[#374151]">
                                {row.average_pct != null ? `${row.average_pct}%` : "—"}
                              </td>
                              <td className="py-3 pr-3 text-right tabular-nums text-[#374151]">
                                {row.below_minimum_count.toLocaleString("en-IN")}
                              </td>
                              <td className="py-3 pr-5">
                                <TrendPill row={row} />
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="px-5 py-10 text-center text-sm text-[#9ca3af]">
                      No department attendance data for the current term.
                    </p>
                  )}
                  <div className="border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
                    {data.department_table_footer_label}
                  </div>
                </section>

                <section className="rounded-xl border border-[#e8ecf2] bg-white p-4 shadow-[0_1px_2px_rgba(15,23,42,0.04)] sm:p-5">
                  <h3 className="mb-4 text-[14px] font-semibold text-[#111827]">{data.trend_chart_title}</h3>
                  <AttendanceTrendChart points={data.trend_series} />
                </section>
              </div>

              <section className="h-fit rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <h3 className="mb-2 text-[14px] font-semibold text-[#111827]">{data.needs_attention_title}</h3>
                <ul>
                  {data.needs_attention_items.map((item) => (
                    <AttentionRow key={item.key} item={item} />
                  ))}
                </ul>
              </section>
            </div>

            <footer className="flex flex-wrap items-center justify-between gap-2 border-t border-[#e8ecf2] pt-4 text-[11px] text-[#9ca3af]">
              <span>{data.footer_disclaimer}</span>
              <span className="tabular-nums">{data.footer_snapshot_label}</span>
            </footer>
          </>
        ) : null}
      </QueryState>
    </div>
  );
}