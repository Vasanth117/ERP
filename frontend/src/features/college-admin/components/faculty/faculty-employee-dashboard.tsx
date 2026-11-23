"use client";
import { CollegeAdminPlusActionLabel } from "@/features/college-admin/components/ui/college-admin-plus-action";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { CalendarIcon } from "@/components/icons/erp/generated/calendar";
import { FilterIcon } from "@/components/icons/erp/generated/filter";
import { Button } from "@/components/ui/button";
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
import { useFacultyEmployeeDashboardPage } from "@/features/college-admin/hooks/use-faculty-employee-dashboard";
import type {
  FacultyEmployeeDesignationBar,
  FacultyEmployeeDashboardPagination,
} from "@/features/college-admin/types/faculty-employee-dashboard";
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

function DesignationBars({ bars }: { bars: FacultyEmployeeDesignationBar[] }) {
  if (!bars.length) {
    return <p className="text-sm text-[#9ca3af]">No designation breakdown yet.</p>;
  }
  const max = Math.max(...bars.map((b) => b.max_value), 1);
  return (
    <ul className="space-y-3.5">
      {bars.map((bar) => (
        <li key={bar.key}>
          <div className="mb-1 flex items-center justify-between text-[12px]">
            <span className="font-medium text-[#374151]">{bar.label}</span>
            <span className="tabular-nums text-[#6b7280]">{bar.value.toLocaleString("en-IN")}</span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-[#eef2f7]">
            <div
              className="h-full rounded-full bg-[#245dd8]"
              style={{ width: `${Math.max(4, (bar.value / max) * 100)}%` }}
            />
          </div>
        </li>
      ))}
    </ul>
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
        <span className="inline-flex min-w-[1.5rem] items-center justify-center rounded-md bg-[#f3f4f6] px-1.5 py-0.5 text-[11px] font-semibold tabular-nums text-[#374151]">
          {item.count.toLocaleString("en-IN")}
        </span>
        <Link href={item.href} className="text-[12px] font-medium text-[#245dd8] hover:underline">
          {item.action_label}
        </Link>
      </div>
    </li>
  );
}

function TablePagination({
  pagination,
  onPage,
}: {
  pagination: FacultyEmployeeDashboardPagination;
  onPage: (page: number) => void;
}) {
  if (pagination.total_pages <= 1) return null;
  return (
    <nav className="flex flex-wrap items-center justify-end gap-1" aria-label="Faculty table pagination">
      {pagination.page_numbers.map((num, idx) =>
        num === -1 ? (
          <span key={`ellipsis-${idx}`} className="px-1 text-[12px] text-[#9ca3af]">
            …
          </span>
        ) : (
          <button
            key={num}
            type="button"
            onClick={() => onPage(num)}
            className={cn(
              "min-w-[1.75rem] rounded px-1.5 py-0.5 text-[12px] tabular-nums",
              num === pagination.page
                ? "bg-[#245dd8] font-medium text-white"
                : "text-[#6b7280] hover:bg-[#f3f4f6]",
            )}
          >
            {num}
          </button>
        ),
      )}
    </nav>
  );
}

function formatAyLabel(label: string) {
  return label.replace(/-/g, "–");
}


export function FacultyEmployeeDashboard() {
  const [academicYear, setAcademicYear] = useState("");
  const [departmentId, setDepartmentId] = useState("");
  const [page, setPage] = useState(1);

  const queryParams = {
    academic_year_code: academicYear || undefined,
    department_id: departmentId || undefined,
    page,
  };

  const { data, isLoading, isError, error, refetch } = useFacultyEmployeeDashboardPage(queryParams);

  useEffect(() => {
    if (data?.selected_academic_year && !academicYear) {
      setAcademicYear(data.selected_academic_year);
    }
  }, [data?.selected_academic_year, academicYear]);

  useEffect(() => {
    setPage(1);
  }, [academicYear, departmentId]);

  const handleExport = useCallback(() => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `faculty-employee-dashboard-${new Date(data.generated_at).toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data]);

  return (
    <div className="space-y-5" data-figma-frame="159:2199">
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
            label={data?.department_filter_label ?? "Department"}
            value={departmentId}
            onChange={setDepartmentId}
            options={data?.department_options ?? [{ value: "", label: "All departments" }]}
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
            href={data?.add_faculty_href ?? "/college-admin/faculty/add-new-faculty-employee"}
            className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
          >
            <CollegeAdminPlusActionLabel iconClassName="size-3.5" label={data?.add_faculty_label ?? "Add faculty / employee" } />
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

            <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_360px]">
              <div className="space-y-5">
                <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                  <div className="flex items-center justify-between border-b border-[#f1f5f9] px-5 py-3.5">
                    <h3 className="text-[14px] font-semibold text-[#111827]">{data.faculty_table_title}</h3>
                    <Link
                      href={data.faculty_view_all_href}
                      className="text-[12px] font-medium text-[#245dd8] hover:underline"
                    >
                      All faculty →
                    </Link>
                  </div>
                  {data.faculty_rows.length ? (
                    <div className="overflow-x-auto">
                      <table className="w-full min-w-[42rem] text-left text-[13px]">
                        <thead>
                          <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                            {data.faculty_table_headers.map((header, index) => (
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
                          {data.faculty_rows.map((row) => (
                            <tr key={row.record_id} className="hover:bg-[#f9fafb]">
                              <td className="px-5 py-3 font-medium text-[#111827]">
                                <Link href={row.detail_href} className="hover:text-[#245dd8]">
                                  {row.faculty_name}
                                </Link>
                              </td>
                              <td className="py-3 pr-3 tabular-nums text-[#374151]">{row.employee_id_label}</td>
                              <td className="py-3 pr-3 text-[#374151]">{row.department_label}</td>
                              <td className="py-3 pr-3 text-[#374151]">{row.designation_label}</td>
                              <td className="py-3 pr-3 tabular-nums text-[#374151]">{row.workload_label}</td>
                              <td className="py-3 pr-5">
                                <StatusPill label={row.status_label} tone={row.status_tone} />
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="px-5 py-10 text-center text-sm text-[#9ca3af]">No faculty in scope.</p>
                  )}
                  <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] px-5 py-3">
                    <Link
                      href={data.faculty_view_all_href}
                      className="text-[12px] font-medium text-[#245dd8] hover:underline"
                    >
                      {data.faculty_view_all_label}
                    </Link>
                    <TablePagination pagination={data.faculty_table_pagination} onPage={setPage} />
                  </div>
                </section>

                <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                  <h3 className="mb-4 text-[14px] font-semibold text-[#111827]">{data.designation_section_title}</h3>
                  <DesignationBars bars={data.designation_bars} />
                </section>
              </div>

              <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <h3 className="mb-1 text-[14px] font-semibold text-[#111827]">{data.needs_attention_title}</h3>
                <ul>
                  {data.needs_attention_items.map((item) => (
                    <AttentionRow key={item.key} item={item} />
                  ))}
                </ul>
              </section>
            </div>

          </>
        ) : null}
      </QueryState>
    </div>
  );
}