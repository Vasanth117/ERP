"use client";

import { CollegeAdminModulePageLayout } from "@/features/college-admin/components/layout/college-admin-module-page-layout";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { SearchIcon } from "@/components/icons/erp/generated/search";
import { Input } from "@/components/ui/input";
import { CollegeAdminPlusActionLabel } from "@/features/college-admin/components/ui/college-admin-plus-action";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useLmsCourseManagementPage } from "@/features/college-admin/hooks/use-lms-courses-mapping";
import type { LmsCourseManagementPage } from "@/features/college-admin/types/lms-courses-mapping";
import type { PoliciesPagination } from "@/features/college-admin/types/institution";
import { cn } from "@/lib/utils";

function StatusPill({ label, tone }: { label: string; tone: string }) {
  const styles: Record<string, string> = {
    success: "bg-[#ecfdf5] text-[#047857]",
    warning: "bg-[#fff7ed] text-[#c2410c]",
    info: "bg-[#eff6ff] text-[#1d4ed8]",
    muted: "bg-[#f3f4f6] text-[#6b7280]",
  };
  const dot: Record<string, string> = {
    success: "bg-[#10b981]",
    warning: "bg-[#f97316]",
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

function FilterSelect({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <select
      aria-label={label}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="h-9 min-w-[8.5rem] rounded-md border border-[#dce3ec] bg-white px-3 text-[13px] text-[#374151]"
    >
      {options.map((opt) => (
        <option key={`${opt.value}-${opt.label}`} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  );
}

function TablePagination({
  pagination,
  onPage,
}: {
  pagination: PoliciesPagination;
  onPage: (page: number) => void;
}) {
  if (pagination.total_pages <= 0) return null;
  return (
    <nav className="flex flex-wrap items-center justify-end gap-1" aria-label="Courses pagination">
      <button
        type="button"
        className="rounded border border-[#dce3ec] px-2 py-1 text-[12px] disabled:opacity-40"
        disabled={!pagination.has_previous}
        onClick={() => onPage(Math.max(1, pagination.page - 1))}
      >
        ‹
      </button>
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
      <button
        type="button"
        className="rounded border border-[#dce3ec] px-2 py-1 text-[12px] disabled:opacity-40"
        disabled={!pagination.has_next}
        onClick={() => onPage(pagination.page + 1)}
      >
        ›
      </button>
    </nav>
  );
}

const emptyPagination: PoliciesPagination = {
  page: 1,
  page_size: 4,
  total: 0,
  total_pages: 0,
  page_numbers: [],
  has_previous: false,
  has_next: false,
};

function mergeView(data: LmsCourseManagementPage | undefined) {
  return {
    page_title: data?.page_title ?? "",
    page_subtitle: data?.page_subtitle ?? "",
    primary_action_label: data?.primary_action_label ?? "",
    primary_action_href: data?.primary_action_href ?? "#",
    search_placeholder: data?.search_placeholder ?? "",
    department_filter_label: data?.department_filter_label ?? "",
    status_filter_label: data?.status_filter_label ?? "",
    department_options: data?.department_options ?? [],
    status_options: data?.status_options ?? [],
    courses_section_title: data?.courses_section_title ?? "",
    table_headers: data?.table_headers ?? [],
    course_rows: data?.course_rows ?? [],
    empty_table_message: data?.empty_table_message ?? "",
    showing_label: data?.showing_label ?? "",
    pagination: data?.pagination ?? emptyPagination,
  };
}

export function LmsCourseManagementDashboard() {
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [department, setDepartment] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedSearch(search.trim()), 300);
    return () => window.clearTimeout(timer);
  }, [search]);

  useEffect(() => {
    setPage(1);
  }, [debouncedSearch, department, status]);

  const queryParams = useMemo(
    () => ({
      page,
      page_size: 4,
      search: debouncedSearch || undefined,
      department: department || undefined,
      status: status || undefined,
    }),
    [page, debouncedSearch, department, status],
  );

  const { data, isLoading, isError, error, refetch, isFetching } = useLmsCourseManagementPage(queryParams);
  const view = mergeView(data);

  return (
    <CollegeAdminModulePageLayout figmaFrame="161:11386">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {view.page_title || "Course Management"}
          </h2>
          {view.page_subtitle ? (
            <p className="mt-1 text-[14px] text-[#6b7280]">{view.page_subtitle}</p>
          ) : null}
        </div>
        <Link
          href={view.primary_action_href}
          className="inline-flex h-9 shrink-0 items-center rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
        >
          <CollegeAdminPlusActionLabel label={view.primary_action_label || "Create course"} />
        </Link>
      </div>

      {isLoading || isFetching ? (
        <p className="text-[12px] text-[#9ca3af]">{isLoading ? "Loading courses…" : "Updating…"}</p>
      ) : null}

      {isError ? (
        <QueryState isError={isError} error={error} onRetry={() => void refetch()}>
          <></>
        </QueryState>
      ) : !data ? null : (
        <>
          <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
            <div className="relative min-w-[14rem] flex-1 sm:max-w-md">
              <SearchIcon className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-[#9ca3af]" />
              <Input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder={view.search_placeholder}
                className="h-9 border-[#dce3ec] pl-9 text-[13px]"
              />
            </div>
            <FilterSelect
              label={view.department_filter_label}
              value={department}
              onChange={setDepartment}
              options={view.department_options}
            />
            <FilterSelect
              label={view.status_filter_label}
              value={status}
              onChange={setStatus}
              options={view.status_options}
            />
          </div>

          <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
            <div className="border-b border-[#f1f5f9] px-5 py-3.5">
              <h3 className="text-[14px] font-semibold text-[#111827]">{view.courses_section_title}</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[52rem] text-left text-[13px]">
                <thead>
                  <tr className="border-b border-[#f1f5f9] bg-[#f9fafb] text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                    {view.table_headers.map((header, index, headers) => (
                      <th
                        key={header}
                        className={cn(
                          "pb-3 pt-3 font-medium",
                          index === 0 ? "pl-5 pr-3" : "pr-3",
                          index === headers.length - 1 ? "pr-5" : "",
                          header === "Students" ? "text-right tabular-nums" : "",
                        )}
                      >
                        {header}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#f1f5f9]">
                  {view.course_rows.length ? (
                    view.course_rows.map((row) => (
                      <tr key={row.row_key} className="text-[#374151] hover:bg-[#f9fafb]">
                        <td className="max-w-[16rem] truncate pl-5 py-3 pr-3 font-medium text-[#111827]">
                          <Link href={row.detail_href} className="text-[#245dd8] hover:underline">
                            {row.course_label}
                          </Link>
                        </td>
                        <td className="py-3 pr-3 tabular-nums text-[#6b7280]">{row.course_code}</td>
                        <td className="py-3 pr-3 text-[#6b7280]">{row.department_label}</td>
                        <td className="py-3 pr-3 text-[#6b7280]">{row.faculty_label}</td>
                        <td className="py-3 pr-3 text-right tabular-nums text-[#374151]">{row.students_count}</td>
                        <td className="py-3 pr-5">
                          <StatusPill label={row.status_label} tone={row.status_tone} />
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td
                        colSpan={Math.max(view.table_headers.length, 1)}
                        className="px-5 py-10 text-center text-sm text-[#9ca3af]"
                      >
                        {view.empty_table_message}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
            <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
              <span>{view.showing_label}</span>
              <TablePagination
                pagination={view.pagination}
                onPage={(p) => {
                  setPage(p);
                }}
              />
            </div>
          </section>
        </>
      )}
    </CollegeAdminModulePageLayout>
  );
}