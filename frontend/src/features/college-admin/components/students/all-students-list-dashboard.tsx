"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { PlusIcon } from "@/components/icons/erp/generated/plus";
import { SearchIcon } from "@/components/icons/erp/generated/search";
import { Input } from "@/components/ui/input";
import { CollegeAdminDownload } from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useAllStudentsListPage } from "@/features/college-admin/hooks/use-all-students-list";
import { cn } from "@/lib/utils";

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
      className="h-9 min-w-[7.5rem] rounded-md border border-[#dce3ec] bg-white px-3 text-[13px] text-[#374151]"
    >
      {options.map((opt) => (
        <option key={`${opt.value}-${opt.label}`} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
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
  if (label === "—") {
    return <span className="text-[#9ca3af]">—</span>;
  }
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


export function AllStudentsListDashboard() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [programme, setProgramme] = useState("");
  const [studyYear, setStudyYear] = useState("");
  const [section, setSection] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  useEffect(() => {
    const t = window.setTimeout(() => setDebouncedSearch(search.trim()), 300);
    return () => window.clearTimeout(t);
  }, [search]);

  useEffect(() => {
    setPage(1);
  }, [debouncedSearch, programme, studyYear, section, statusFilter]);

  const { data, isLoading, isError, error, refetch } = useAllStudentsListPage({
    page,
    search: debouncedSearch || undefined,
    programme_code: programme || undefined,
    study_year: studyYear || undefined,
    section_code: section || undefined,
    status_filter: statusFilter || undefined,
  });

  const handleExport = useCallback(() => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `all-students-${new Date(data.generated_at).toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data]);

  const headers = data?.table_headers ?? [];

  return (
    <div className="space-y-5" data-figma-frame="69:145896">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "All Students List"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">
            {data?.page_subtitle ?? "Search and manage every student record in the college"}
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <button
            type="button"
            onClick={handleExport}
            disabled={!data}
            className="inline-flex h-9 items-center gap-1.5 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb] disabled:opacity-50"
          >
            <CollegeAdminDownload className="size-3.5" />
            {data?.export_label ?? "Export"}
          </button>
          <Link
            href={data?.add_student_href ?? "/college-admin/students/create-student"}
            className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
          >
            <PlusIcon className="size-3.5" aria-hidden />
            {data?.add_student_label ?? "Add student"}
          </Link>
        </div>
      </div>

      <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
        <div className="relative max-w-xl flex-1">
          <SearchIcon className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-[#9ca3af]" />
          <Input
            className="h-9 pl-9"
            placeholder={data?.search_placeholder ?? "Search name, register number, phone or email..."}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        {data ? (
          <div className="flex flex-wrap items-center gap-2">
            <FilterSelect
              label={data.programme_filter_label}
              value={programme}
              onChange={setProgramme}
              options={data.programme_options}
            />
            <FilterSelect
              label={data.year_filter_label}
              value={studyYear}
              onChange={setStudyYear}
              options={data.year_options}
            />
            <FilterSelect
              label={data.section_filter_label}
              value={section}
              onChange={setSection}
              options={data.section_options}
            />
            <FilterSelect
              label={data.status_filter_label}
              value={statusFilter}
              onChange={setStatusFilter}
              options={data.status_options}
            />
            <Link
              href={data.bulk_actions_href}
              className="inline-flex h-9 items-center rounded-md border border-[#dce3ec] bg-white px-3 text-xs font-medium text-[#374151] hover:bg-[#f9fafb]"
            >
              {data.bulk_actions_label} …
            </Link>
          </div>
        ) : null}
      </div>

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="flex items-center justify-between border-b border-[#f1f5f9] px-5 py-3.5">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.students_section_title}</h3>
                <span className="text-[12px] text-[#6b7280]">{data.students_count_label}</span>
              </div>
              {data.students.length ? (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[52rem] text-left text-[13px]">
                    <thead>
                      <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                        {headers.map((header, index) => (
                          <th
                            key={header}
                            className={cn(
                              "pb-3 font-medium",
                              index === 0 ? "px-5" : "pr-3",
                              index === headers.length - 1 ? "pr-5" : "",
                            )}
                          >
                            {header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#f1f5f9]">
                      {data.students.map((row) => (
                        <tr key={row.record_id} className="hover:bg-[#f9fafb]">
                          <td className="px-5 py-3 font-medium text-[#111827]">
                            <Link href={row.detail_href} className="hover:text-[#245dd8]">
                              {row.student_name}
                            </Link>
                          </td>
                          <td className="py-3 pr-3 font-mono text-[12px] text-[#374151]">{row.register_number}</td>
                          <td className="py-3 pr-3 text-[#374151]">{row.programme_label}</td>
                          <td className="py-3 pr-3 tabular-nums text-[#374151]">{row.year_section_label}</td>
                          <td
                            className={cn(
                              "py-3 pr-3 tabular-nums font-medium",
                              row.attendance_tone === "warning"
                                ? "text-[#c2410c]"
                                : row.attendance_tone === "success"
                                  ? "text-[#047857]"
                                  : "text-[#6b7280]",
                            )}
                          >
                            {row.attendance_label}
                          </td>
                          <td className="py-3 pr-3">
                            <StatusPill label={row.fee_status_label} tone={row.fee_status_tone} />
                          </td>
                          <td className="py-3 pr-5">
                            <StatusPill label={row.status_label} tone={row.status_tone} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="px-5 py-8 text-sm text-[#9ca3af]">No students match your search and filters.</p>
              )}
              <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
                <span>{data.showing_label}</span>
                {data.pagination.total_pages > 0 ? (
                  <div className="flex items-center gap-1">
                    <button
                      type="button"
                      className="rounded border border-[#dce3ec] px-2 py-1 disabled:opacity-40"
                      disabled={!data.pagination.has_previous}
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                    >
                      ‹
                    </button>
                    {data.pagination.page_numbers.map((num, index) =>
                      num === -1 ? (
                        <span key={`ellipsis-${index}`} className="px-1">
                          …
                        </span>
                      ) : (
                        <button
                          key={num}
                          type="button"
                          className={cn(
                            "min-w-8 rounded border px-2 py-1 tabular-nums",
                            num === data.pagination.page
                              ? "border-[#245dd8] bg-[#eff6ff] text-[#245dd8]"
                              : "border-[#dce3ec]",
                          )}
                          onClick={() => setPage(num)}
                        >
                          {num}
                        </button>
                      ),
                    )}
                    <button
                      type="button"
                      className="rounded border border-[#dce3ec] px-2 py-1 disabled:opacity-40"
                      disabled={!data.pagination.has_next}
                      onClick={() => setPage((p) => p + 1)}
                    >
                      ›
                    </button>
                  </div>
                ) : null}
              </div>
            </section>

          </>
        ) : null}
      </QueryState>
    </div>
  );
}