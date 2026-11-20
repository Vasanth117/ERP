"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

import { CalendarDaysIcon } from "@/components/icons/erp/generated/calendar-days";
import { FilterIcon } from "@/components/icons/erp/generated/filter";
import { PlusIcon } from "@/components/icons/erp/generated/plus";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { CollegeAdminDownload } from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useDepartmentFacultyAllocationPage,
  useSaveDepartmentFacultyAllocation,
} from "@/features/college-admin/hooks/use-department-faculty-allocation";
import type { DepartmentFacultyAllocationFormValues } from "@/features/college-admin/types/department-faculty-allocation";
import { cn } from "@/lib/utils";

function StatusPill({ label, tone }: { label: string; tone: string }) {
  const styles: Record<string, string> = {
    success: "bg-[#ecfdf5] text-[#047857]",
    warning: "bg-[#fff7ed] text-[#c2410c]",
    error: "bg-[#fef2f2] text-[#b91c1c]",
    muted: "bg-[#f3f4f6] text-[#6b7280]",
  };
  const dot: Record<string, string> = {
    success: "bg-[#10b981]",
    warning: "bg-[#f97316]",
    error: "bg-[#ef4444]",
    muted: "bg-[#9ca3af]",
  };
  const key = tone in styles ? tone : "muted";
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-medium", styles[key])}>
      <span className={cn("size-1.5 rounded-full", dot[key])} />
      {label}
    </span>
  );
}

function CountBadge({ count, tone }: { count: number; tone: string }) {
  const styles = tone === "warning" ? "bg-[#fff7ed] text-[#c2410c]" : "bg-[#eff6ff] text-[#1d4ed8]";
  return (
    <span className={cn("rounded-full px-2 py-0.5 text-[11px] font-semibold tabular-nums", styles)}>{count}</span>
  );
}

function formatSnapshot(iso: string) {
  try {
    return new Intl.DateTimeFormat("en-IN", {
      dateStyle: "medium",
      timeStyle: "short",
      timeZone: "Asia/Kolkata",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

function FilterSelect({
  icon,
  label,
  value,
  onChange,
  options,
}: {
  icon?: React.ReactNode;
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
      className="inline-flex h-9 min-w-[9rem] items-center gap-1.5 rounded-md border border-[#dce3ec] bg-white px-3 text-[13px] text-[#374151]"
    >
      {options.map((opt) => (
        <option key={`${opt.value}-${opt.label}`} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  );
}

export function DepartmentFacultyAllocationDashboard() {
  const [page, setPage] = useState(1);
  const [semester, setSemester] = useState("");
  const [departmentId, setDepartmentId] = useState("");
  const [designation, setDesignation] = useState("");
  const [formDraft, setFormDraft] = useState<DepartmentFacultyAllocationFormValues | null>(null);

  const queryParams = useMemo(
    () => ({
      page,
      semester_label: semester || undefined,
      department_id: departmentId || undefined,
      designation_filter: designation || undefined,
    }),
    [page, semester, departmentId, designation],
  );

  const { data, isLoading, isError, error, refetch, isFetching } = useDepartmentFacultyAllocationPage(queryParams);
  const save = useSaveDepartmentFacultyAllocation();

  useEffect(() => {
    if (!data) return;
    if (!semester && data.selected_semester) setSemester(data.selected_semester);
    setFormDraft((prev) => prev ?? { ...data.form });
  }, [data, semester]);

  const form = formDraft ?? data?.form;

  const handleExport = useCallback(() => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `faculty-allocation-${new Date(data.generated_at).toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data]);

  const headers = data?.capacity_table_headers ?? ["Department", "Sanctioned", "In position", "Vacant", "Workload", "Status"];

  const scrollToForm = () => {
    document.getElementById("move-share-faculty")?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const handleSave = () => {
    if (!form) return;
    save.mutate(
      { form },
      {
        onSuccess: (result) => {
          toast.success(result.message);
          setFormDraft({ ...result.page.form });
        },
        onError: (e: Error) => toast.error(e.message),
      },
    );
  };

  return (
    <div className="space-y-5" data-figma-frame="69:134506">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Department Faculty Allocation"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">
            {data?.page_subtitle ?? "Allocate faculty to departments and balance teaching capacity"}
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <button
            type="button"
            className="inline-flex h-9 items-center gap-1.5 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb] disabled:opacity-50"
            onClick={handleExport}
            disabled={isLoading || !data}
          >
            <CollegeAdminDownload className="size-3.5" aria-hidden />
            {data?.export_label ?? "Export"}
          </button>
          <button
            type="button"
            className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
            onClick={scrollToForm}
          >
            <PlusIcon className="size-3.5" aria-hidden />
            {data?.allocate_faculty_label ?? "+ Allocate faculty"}
          </button>
        </div>
      </div>

      {data ? (
        <div className="flex flex-col gap-3 lg:flex-row lg:flex-wrap lg:items-center lg:justify-between">
          <div className="flex flex-wrap items-center gap-2">
            <span className="mr-1 inline-flex items-center gap-1 text-[12px] text-[#6b7280]">
              <CalendarDaysIcon className="size-3.5" aria-hidden />
              {data.semester_filter_label}
            </span>
            <FilterSelect
              label={data.semester_filter_label}
              value={semester}
              onChange={(v) => {
                setSemester(v);
                setPage(1);
              }}
              options={data.semester_options}
            />
            <FilterSelect
              icon={<FilterIcon className="size-3.5" aria-hidden />}
              label={data.department_filter_label}
              value={departmentId}
              onChange={(v) => {
                setDepartmentId(v);
                setPage(1);
              }}
              options={data.department_options}
            />
            <FilterSelect
              label={data.designation_filter_label}
              value={designation}
              onChange={(v) => {
                setDesignation(v);
                setPage(1);
              }}
              options={data.designation_options}
            />
            <Link
              href={
                departmentId
                  ? `${data.resources_nav_href}?departmentId=${encodeURIComponent(departmentId)}`
                  : data.resources_nav_href
              }
              className="ml-2 inline-flex h-9 items-center rounded-md border border-[#dce3ec] bg-white px-4 text-[13px] font-medium text-[#245dd8] hover:bg-[#eff6ff]"
            >
              {data.resources_nav_label}
            </Link>
          </div>
          <span className="text-[12px] tabular-nums text-[#9ca3af]">{data.updated_at_label}</span>
        </div>
      ) : null}

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()} isEmpty={false}>
        {data && form ? (
          <div className={cn("grid gap-5 xl:grid-cols-[minmax(0,1fr)_18rem]", isFetching && "opacity-70")}>
            <div className="space-y-5">
              <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                  <h3 className="text-[14px] font-semibold text-[#111827]">{data.capacity_section_title}</h3>
                </div>
                {data.capacity_rows.length ? (
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[40rem] text-left text-[13px]">
                      <thead>
                        <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                          {headers.map((h, i) => (
                            <th key={h} className={cn("pb-3 font-medium", i === 0 ? "px-5" : "pr-3", i === headers.length - 1 ? "pr-5" : "")}>
                              {h}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#f1f5f9]">
                        {data.capacity_rows.map((row) => (
                          <tr key={row.department_id} className="hover:bg-[#f9fafb]">
                            <td className="px-5 py-3 font-semibold text-[#111827]">{row.department_label}</td>
                            <td className="py-3 pr-3 tabular-nums text-[#374151]">{row.sanctioned}</td>
                            <td className="py-3 pr-3 tabular-nums text-[#374151]">{row.in_position}</td>
                            <td className="py-3 pr-3 tabular-nums text-[#374151]">{row.vacant}</td>
                            <td className="py-3 pr-3 tabular-nums text-[#374151]">
                              {row.workload_pct != null ? `${row.workload_pct}%` : "—"}
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
                  <p className="px-5 py-8 text-sm text-[#9ca3af]">No departments match the selected filters.</p>
                )}
                <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] px-5 py-3 text-[11px] text-[#9ca3af]">
                  <span>{data.capacity_table_footer_note}</span>
                  {data.pagination.total_pages > 0 ? (
                    <div className="flex items-center gap-1 text-[12px] text-[#6b7280]">
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

              <section
                id="move-share-faculty"
                className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]"
              >
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.move_share_section_title}</h3>
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  <FieldSelect
                    label={data.faculty_field_label}
                    required
                    value={form.faculty_user_id}
                    options={data.faculty_options}
                    onChange={(value) => setFormDraft({ ...form, faculty_user_id: value })}
                  />
                  <FieldSelect
                    label={data.allocate_to_field_label}
                    required
                    value={form.allocate_to_department_id}
                    options={data.department_allocate_options}
                    onChange={(value) => setFormDraft({ ...form, allocate_to_department_id: value })}
                  />
                  <FieldSelect
                    label={data.allocation_type_field_label}
                    required
                    value={form.allocation_type}
                    options={data.allocation_type_options}
                    onChange={(value) => setFormDraft({ ...form, allocation_type: value })}
                  />
                  <FieldDate
                    label={data.effective_from_field_label}
                    required
                    value={form.effective_from.slice(0, 10)}
                    onChange={(value) => setFormDraft({ ...form, effective_from: value })}
                  />
                </div>
                <p className="mt-4 text-[11px] text-[#9ca3af]">{data.move_footer_note}</p>
                <div className="mt-4 flex justify-end gap-2">
                  <button
                    type="button"
                    className="h-9 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151]"
                    onClick={() => setFormDraft({ ...data.form })}
                  >
                    {data.cancel_label}
                  </button>
                  <button
                    type="button"
                    className="h-9 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8] disabled:opacity-50"
                    disabled={
                      !form.faculty_user_id ||
                      !form.allocate_to_department_id ||
                      save.isPending
                    }
                    onClick={handleSave}
                  >
                    {data.save_label}
                  </button>
                </div>
              </section>
            </div>

            <aside className="space-y-4">
              <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <div className="flex items-center justify-between">
                  <h3 className="text-[14px] font-semibold text-[#111827]">{data.vacancies_section_title}</h3>
                  <Link href={data.hr_recruitment_href} className="text-[12px] font-medium text-[#245dd8] hover:underline">
                    {data.hr_recruitment_label}
                  </Link>
                </div>
                <ul className="mt-3 space-y-3">
                  {data.vacancy_items.length ? (
                    data.vacancy_items.map((item) => (
                      <li key={item.department_id} className="flex items-start justify-between gap-2 border-b border-[#f1f5f9] pb-3 last:border-0 last:pb-0">
                        <div className="min-w-0">
                          <p className="text-[13px] font-semibold text-[#111827]">{item.department_label}</p>
                          <p className="mt-0.5 text-[12px] text-[#6b7280]">{item.detail}</p>
                        </div>
                        <CountBadge count={item.count} tone={item.badge_tone} />
                      </li>
                    ))
                  ) : (
                    <li className="text-[13px] text-[#9ca3af]">No open faculty vacancies.</li>
                  )}
                </ul>
              </section>

              <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.designation_mix_section_title}</h3>
                <ul className="mt-4 space-y-3">
                  {data.designation_bars.map((bar) => (
                    <li key={bar.key}>
                      <div className="flex items-center justify-between text-[12px] text-[#6b7280]">
                        <span>{bar.label}</span>
                        <span className="font-semibold tabular-nums text-[#111827]">{bar.value}</span>
                      </div>
                      <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-[#e5e7eb]">
                        <div
                          className="h-full rounded-full bg-[#245dd8]"
                          style={{ width: `${bar.max_value ? (bar.value / bar.max_value) * 100 : 0}%` }}
                        />
                      </div>
                    </li>
                  ))}
                </ul>
              </section>
            </aside>
          </div>
        ) : null}
      </QueryState>

      {data ? (
        <footer className="flex flex-col gap-2 border-t border-[#e8ecf2] pt-4 text-[11px] text-[#9ca3af] sm:flex-row sm:items-center sm:justify-between">
          <p>{data.footer_disclaimer}</p>
          <p className="tabular-nums">
            {data.footer_snapshot_label} · {formatSnapshot(data.generated_at)}
          </p>
        </footer>
      ) : null}
    </div>
  );
}

function FieldSelect({
  label,
  required,
  value,
  options,
  onChange,
}: {
  label: string;
  required?: boolean;
  value: string;
  options: { value: string; label: string }[];
  onChange: (value: string) => void;
}) {
  return (
    <div className="space-y-1">
      <Label className="text-[12px] text-[#374151]">
        {label} {required ? <span className="text-[#dc2626]">*</span> : null}
      </Label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="h-9 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px] text-[#374151]"
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

function FieldDate({
  label,
  required,
  value,
  onChange,
}: {
  label: string;
  required?: boolean;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <div className="space-y-1">
      <Label className="text-[12px] text-[#374151]">
        {label} {required ? <span className="text-[#dc2626]">*</span> : null}
      </Label>
      <Input
        type="date"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="h-9 border-[#dce3ec] text-[13px]"
      />
    </div>
  );
}