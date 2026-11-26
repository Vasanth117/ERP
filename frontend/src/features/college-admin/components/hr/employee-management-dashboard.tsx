"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { SearchIcon } from "@/components/icons/erp/generated/search";
import { Input } from "@/components/ui/input";
import { CollegeAdminPlusActionLabel } from "@/features/college-admin/components/ui/college-admin-plus-action";
import { CollegeAdminDownload } from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useHrEmployeeManagementPage } from "@/features/college-admin/hooks/use-hr-employee-management";
import type { EmployeeDirectoryPage } from "@/features/college-admin/types/employee-directory";
import { cn } from "@/lib/utils";

const TABLE_HEADERS = ["Employee", "ID", "Department", "Designation", "Type", "Status"];

const DEFAULT_TYPE_OPTIONS = [
  { value: "", label: "All types" },
  { value: "permanent", label: "Permanent" },
  { value: "probation", label: "Probation" },
  { value: "contract", label: "Contract" },
];

const DEFAULT_STATUS_OPTIONS = [
  { value: "", label: "All statuses" },
  { value: "active", label: "Active" },
  { value: "probation", label: "Probation" },
  { value: "notice", label: "Notice" },
  { value: "on_leave", label: "On leave" },
];

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
      className="h-9 min-w-[9rem] rounded-md border border-[#dce3ec] bg-white px-3 text-[13px] text-[#374151]"
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

function mergeView(data: EmployeeDirectoryPage | undefined) {
  return {
    page_title: data?.page_title ?? "Employee Management",
    page_subtitle: data?.page_subtitle ?? "Directory, status and records",
    export_label: data?.export_label ?? "Export",
    add_employee_label: data?.add_employee_label ?? "Add employee",
    add_employee_href: data?.add_employee_href ?? "/college-admin/faculty/add-new-faculty-employee",
    search_placeholder: data?.search_placeholder ?? "Search name, ID or department",
    department_filter_label: data?.unit_filter_label ?? "Department",
    type_filter_label: data?.type_filter_label ?? "Type",
    status_filter_label: data?.status_filter_label ?? "Status",
    department_options: data?.unit_options?.length
      ? data.unit_options
      : [{ value: "", label: "All departments" }],
    type_options: data?.type_options?.length ? data.type_options : DEFAULT_TYPE_OPTIONS,
    status_options: data?.status_options?.length ? data.status_options : DEFAULT_STATUS_OPTIONS,
    employees_section_title: data?.employees_section_title ?? "Employees",
    table_headers: data?.table_headers?.length ? data.table_headers : TABLE_HEADERS,
    employee_rows: data?.employee_rows ?? [],
    showing_label: data?.showing_label ?? "Showing 0 of 0",
    pagination: data?.pagination ?? {
      page: 1,
      page_size: 4,
      total: 0,
      total_pages: 0,
      page_numbers: [],
      has_previous: false,
      has_next: false,
    },
  };
}

export function EmployeeManagementDashboard() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [departmentId, setDepartmentId] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  useEffect(() => {
    const t = window.setTimeout(() => setDebouncedSearch(search.trim()), 300);
    return () => window.clearTimeout(t);
  }, [search]);

  useEffect(() => {
    setPage(1);
  }, [debouncedSearch, departmentId, typeFilter, statusFilter]);

  const queryParams = useMemo(
    () => ({
      page,
      search: debouncedSearch || undefined,
      department_id: departmentId || undefined,
      type_filter: typeFilter || undefined,
      status_filter: statusFilter || undefined,
    }),
    [page, debouncedSearch, departmentId, typeFilter, statusFilter],
  );

  const { data, isLoading, isError, error, refetch, isFetching } = useHrEmployeeManagementPage(queryParams);
  const view = mergeView(data);

  const handleExport = useCallback(() => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `hr-employee-management-${new Date(data.generated_at).toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data]);

  return (
    <div className="space-y-5" data-figma-frame="160:7538">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">{view.page_title}</h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">{view.page_subtitle}</p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <button
            type="button"
            onClick={handleExport}
            disabled={!data}
            className="inline-flex h-9 items-center gap-1.5 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb] disabled:opacity-50"
          >
            <CollegeAdminDownload className="size-3.5" />
            {view.export_label}
          </button>
          <Link
            href={view.add_employee_href}
            className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
          >
            <CollegeAdminPlusActionLabel iconClassName="size-3.5" label={view.add_employee_label} />
          </Link>
        </div>
      </div>

      <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
        <div className="relative max-w-md flex-1">
          <SearchIcon className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-[#9ca3af]" />
          <Input
            className="h-9 pl-9"
            placeholder={view.search_placeholder}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <FilterSelect
            label={view.department_filter_label}
            value={departmentId}
            onChange={setDepartmentId}
            options={view.department_options}
          />
          <FilterSelect
            label={view.type_filter_label}
            value={typeFilter}
            onChange={setTypeFilter}
            options={view.type_options}
          />
          <FilterSelect
            label={view.status_filter_label}
            value={statusFilter}
            onChange={setStatusFilter}
            options={view.status_options}
          />
        </div>
      </div>

      {isLoading || isFetching ? (
        <p className="text-[12px] text-[#9ca3af]">{isLoading ? "Loading employees…" : "Updating…"}</p>
      ) : null}

      {isError ? <QueryState isError={isError} error={error} onRetry={() => void refetch()} /> : null}

      {!isError ? (
        <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
          <div className="flex items-center justify-between border-b border-[#f1f5f9] px-5 py-3.5">
            <h3 className="text-[14px] font-semibold text-[#111827]">{view.employees_section_title}</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[44rem] text-left text-[13px]">
              <thead>
                <tr className="border-b border-[#f1f5f9] text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                  {view.table_headers.map((header, index) => (
                    <th
                      key={header}
                      className={cn(
                        "pb-3 pt-4 font-medium",
                        index === 0 ? "pl-5 pr-3" : "pr-3",
                        index === view.table_headers.length - 1 ? "pr-5" : "",
                      )}
                    >
                      {header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#f1f5f9]">
                {view.employee_rows.length ? (
                  view.employee_rows.map((row) => (
                    <tr key={row.record_id} className="hover:bg-[#f9fafb]">
                      <td className="pl-5 py-3 pr-3 font-medium text-[#111827]">
                        <Link href={row.detail_href} className="hover:text-[#245dd8]">
                          {row.employee_name}
                        </Link>
                      </td>
                      <td className="py-3 pr-3 font-mono text-[12px] text-[#374151]">{row.employee_id_label}</td>
                      <td className="py-3 pr-3 text-[#374151]">{row.unit_label}</td>
                      <td className="py-3 pr-3 text-[#374151]">{row.role_label}</td>
                      <td className="py-3 pr-3 text-[#374151]">{row.type_label}</td>
                      <td className="py-3 pr-5">
                        <StatusPill label={row.status_label} tone={row.status_tone} />
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={view.table_headers.length} className="px-5 py-10 text-center text-sm text-[#9ca3af]">
                      No employees match your search and filters.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
            <span>{view.showing_label}</span>
            {view.pagination.total_pages > 0 ? (
              <div className="flex items-center gap-1">
                <button
                  type="button"
                  className="rounded border border-[#dce3ec] px-2 py-1 disabled:opacity-40"
                  disabled={!view.pagination.has_previous}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                >
                  ‹
                </button>
                {view.pagination.page_numbers.map((num, index) =>
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
                        num === view.pagination.page
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
                  disabled={!view.pagination.has_next}
                  onClick={() => setPage((p) => p + 1)}
                >
                  ›
                </button>
              </div>
            ) : null}
          </div>
        </section>
      ) : null}
    </div>
  );
}