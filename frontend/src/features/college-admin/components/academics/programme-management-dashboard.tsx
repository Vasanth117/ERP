"use client";

import { useCallback, useEffect, useState } from "react";
import { useForm } from "react-hook-form";

import { PlusIcon } from "@/components/icons/erp/generated/plus";
import { SearchIcon } from "@/components/icons/erp/generated/search";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { CollegeAdminDownload } from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useCreateProgrammeManagement,
  useProgrammeManagementPage,
} from "@/features/college-admin/hooks/use-programme-management";
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
    info: "bg-[#eff6ff] text-[#1e40af]",
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
    <span className={cn("inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-medium", styles[key])}>
      <span className={cn("size-1.5 rounded-full", dot[key])} />
      {label}
    </span>
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

type CreateFormValues = {
  name: string;
  programme_code: string;
  department_id: string;
  duration_semesters: string;
  credits_required: string;
};

export function ProgrammeManagementDashboard() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [levelFilter, setLevelFilter] = useState("");
  const [departmentId, setDepartmentId] = useState("");
  const [regulationFilter, setRegulationFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [showCreate, setShowCreate] = useState(false);

  useEffect(() => {
    const t = window.setTimeout(() => setDebouncedSearch(search.trim()), 300);
    return () => window.clearTimeout(t);
  }, [search]);

  useEffect(() => {
    setPage(1);
  }, [debouncedSearch, levelFilter, departmentId, regulationFilter, statusFilter]);

  const { data, isLoading, isError, error, refetch } = useProgrammeManagementPage({
    page,
    search: debouncedSearch || undefined,
    level_filter: levelFilter || undefined,
    department_id: departmentId || undefined,
    regulation_filter: regulationFilter || undefined,
    status_filter: statusFilter || undefined,
  });

  const createProgramme = useCreateProgrammeManagement();

  const form = useForm<CreateFormValues>({
    defaultValues: {
      name: "",
      programme_code: "",
      department_id: "",
      duration_semesters: "8",
      credits_required: "160",
    },
  });

  const handleExport = useCallback(() => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `programme-management-${new Date(data.generated_at).toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data]);

  const onSubmitCreate = (values: CreateFormValues) => {
    createProgramme.mutate(
      {
        name: values.name.trim(),
        programme_code: values.programme_code.trim(),
        department_id: values.department_id || null,
        duration_semesters: Number(values.duration_semesters),
        credits_required: Number(values.credits_required),
      },
      {
        onSuccess: () => {
          setShowCreate(false);
          form.reset();
        },
      },
    );
  };

  const headers = data?.table_headers ?? [];

  return (
    <div className="space-y-5" data-figma-frame="69:140372">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Programme Management"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">
            {data?.page_subtitle ?? "Degree programmes, intake and duration offered by the college"}
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
          <button
            type="button"
            onClick={() => setShowCreate((v) => !v)}
            className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
          >
            <PlusIcon className="size-3.5" aria-hidden />
            {data?.add_programme_label ?? "Add programme"}
          </button>
        </div>
      </div>

      <div className="flex flex-col gap-3 xl:flex-row xl:items-center">
        <div className="relative max-w-xl flex-1">
          <SearchIcon className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-[#9ca3af]" />
          <Input
            className="h-9 pl-9"
            placeholder={data?.search_placeholder ?? "Search programmes..."}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        {data ? (
          <div className="flex flex-wrap items-center gap-2">
            <FilterSelect
              label={data.level_filter_label}
              value={levelFilter}
              onChange={setLevelFilter}
              options={data.level_options}
            />
            <FilterSelect
              label={data.department_filter_label}
              value={departmentId}
              onChange={setDepartmentId}
              options={data.department_options}
            />
            <FilterSelect
              label={data.regulation_filter_label}
              value={regulationFilter}
              onChange={setRegulationFilter}
              options={data.regulation_options}
            />
            <FilterSelect
              label={data.status_filter_label}
              value={statusFilter}
              onChange={setStatusFilter}
              options={data.status_options}
            />
          </div>
        ) : null}
      </div>

      {showCreate && data ? (
        <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
          <h3 className="text-[14px] font-semibold text-[#111827]">{data.create_section_title}</h3>
          <p className="mt-1 text-[12px] text-[#6b7280]">{data.create_form_note}</p>
          <form
            className="mt-4 grid gap-4 sm:grid-cols-2"
            onSubmit={form.handleSubmit(onSubmitCreate)}
          >
            {data.create_fields.map((field) => (
              <div key={field.key} className={field.key === "name" ? "sm:col-span-2" : undefined}>
                <Label className="text-[12px] text-[#374151]">
                  {field.label}
                  {field.required ? " *" : ""}
                </Label>
                {field.field_type === "select" ? (
                  <select
                    className="mt-1 flex h-9 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px]"
                    {...form.register(field.key as keyof CreateFormValues)}
                  >
                    {data.create_department_options.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                ) : (
                  <Input
                    className="mt-1 h-9"
                    type={field.field_type === "number" ? "number" : "text"}
                    required={field.required}
                    {...form.register(field.key as keyof CreateFormValues, {
                      required: field.required,
                    })}
                  />
                )}
              </div>
            ))}
            <div className="flex flex-wrap justify-end gap-2 sm:col-span-2">
              <button
                type="button"
                onClick={() => {
                  setShowCreate(false);
                  form.reset();
                }}
                className="h-9 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151]"
              >
                {data.create_cancel_label}
              </button>
              <button
                type="submit"
                disabled={createProgramme.isPending}
                className="h-9 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8] disabled:opacity-50"
              >
                {data.create_submit_label}
              </button>
            </div>
          </form>
        </section>
      ) : null}

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="flex items-center justify-between border-b border-[#f1f5f9] px-5 py-3.5">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.programmes_section_title}</h3>
                <span className="text-[12px] text-[#6b7280]">{data.programmes_count_label}</span>
              </div>
              {data.programmes.length ? (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[52rem] text-left text-[13px]">
                    <thead>
                      <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                        {headers.map((header, index) => (
                          <th
                            key={header}
                            className={cn(
                              "pb-3 font-medium",
                              index === 0 ? "px-5 pt-4" : "pr-3 pt-4",
                              index === headers.length - 1 ? "pr-5" : "",
                            )}
                          >
                            {header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#f1f5f9]">
                      {data.programmes.map((row) => (
                        <tr key={row.programme_id} className="hover:bg-[#f9fafb]">
                          <td className="px-5 py-3 font-medium text-[#111827]">{row.programme_name}</td>
                          <td className="py-3 pr-3 font-mono text-[12px] text-[#374151]">{row.programme_code}</td>
                          <td className="py-3 pr-3 text-[#374151]">{row.level_label}</td>
                          <td className="py-3 pr-3 text-[#374151]">{row.department_label}</td>
                          <td className="py-3 pr-3 text-[#374151]">{row.duration_label}</td>
                          <td className="py-3 pr-3 tabular-nums text-[#374151]">{row.intake_label}</td>
                          <td className="py-3 pr-3 font-mono text-[12px] text-[#374151]">{row.regulation_label}</td>
                          <td className="py-3 pr-5">
                            <StatusPill label={row.status_label} tone={row.status_tone} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="px-5 py-8 text-sm text-[#9ca3af]">No programmes match your search and filters.</p>
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

            <footer className="flex flex-col gap-2 border-t border-[#e8ecf2] pt-4 text-[11px] text-[#9ca3af] sm:flex-row sm:items-center sm:justify-between">
              <p>{data.footer_disclaimer}</p>
              <p className="tabular-nums">
                {data.footer_snapshot_label} · {formatSnapshot(data.generated_at)}
              </p>
            </footer>
          </>
        ) : null}
      </QueryState>
    </div>
  );
}