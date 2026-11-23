"use client";
import { CollegeAdminPlusActionLabel } from "@/features/college-admin/components/ui/college-admin-plus-action";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { SearchIcon } from "@/components/icons/erp/generated/search";
import { Input } from "@/components/ui/input";
import { CollegeAdminDownload } from "@/features/college-admin/components/layout/college-admin-erp-icons";
import {
  CollegeAdminPrimaryLink,
  CollegeAdminSecondaryButton,
} from "@/features/college-admin/components/ui/college-admin-action-button";
import {
  CollegeAdminPanelEmptyState,
  CollegeAdminTablePanel,
} from "@/features/college-admin/components/ui/dashboard-panel-ui";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useProgrammeManagementPage } from "@/features/college-admin/hooks/use-programme-management";
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

export function ProgrammeManagementDashboard() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [levelFilter, setLevelFilter] = useState("");
  const [departmentId, setDepartmentId] = useState("");
  const [regulationFilter, setRegulationFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

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

  const createHref = data?.new_programme_href ?? "/college-admin/academics/create-programme";
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
        <div className="flex shrink-0 flex-wrap items-center gap-2">
          <CollegeAdminSecondaryButton onClick={handleExport} disabled={!data}>
            <CollegeAdminDownload className="size-3.5" />
            {data?.export_label ?? "Export"}
          </CollegeAdminSecondaryButton>
          <CollegeAdminPrimaryLink href={createHref}>
            <CollegeAdminPlusActionLabel iconClassName="size-3.5" label={data?.add_programme_label ?? "Add programme" } />
          </CollegeAdminPrimaryLink>
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
            <FilterSelect label={data.level_filter_label} value={levelFilter} onChange={setLevelFilter} options={data.level_options} />
            <FilterSelect label={data.department_filter_label} value={departmentId} onChange={setDepartmentId} options={data.department_options} />
            <FilterSelect label={data.regulation_filter_label} value={regulationFilter} onChange={setRegulationFilter} options={data.regulation_options} />
            <FilterSelect label={data.status_filter_label} value={statusFilter} onChange={setStatusFilter} options={data.status_options} />
          </div>
        ) : null}
      </div>

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <CollegeAdminTablePanel
            title={data.programmes_section_title}
            description={data.programmes_count_label}
            footer={
              <>
                <span>{data.showing_label}</span>
                {data.pagination.total_pages > 0 ? (
                  <Pagination data={data} page={page} setPage={setPage} />
                ) : null}
              </>
            }
          >
            {data.programmes.length ? (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[52rem] text-left text-[13px]">
                  <thead>
                    <tr className="border-b border-[#f1f5f9] text-[11px] font-semibold uppercase tracking-wide text-[#94a3b8]">
                      {headers.map((header, index) => (
                        <th
                          key={header}
                          className={cn("pb-3 pt-4 font-medium", index === 0 ? "px-5" : "pr-3", index === headers.length - 1 ? "pr-5" : "")}
                        >
                          {header}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#f1f5f9]">
                    {data.programmes.map((row) => (
                      <tr key={row.programme_id} className="transition-colors hover:bg-[#f8fafc]">
                        <td className="px-5 py-3.5 font-medium text-[#111827]">
                          <Link href={row.detail_href} className="hover:text-[#245dd8]">
                            {row.programme_name}
                          </Link>
                        </td>
                        <td className="py-3.5 pr-3 font-mono text-[12px] text-[#374151]">{row.programme_code}</td>
                        <td className="py-3.5 pr-3 text-[#374151]">{row.level_label}</td>
                        <td className="py-3.5 pr-3 text-[#374151]">{row.department_label}</td>
                        <td className="py-3.5 pr-3 text-[#374151]">{row.duration_label}</td>
                        <td className="py-3.5 pr-3 tabular-nums text-[#374151]">{row.intake_label}</td>
                        <td className="py-3.5 pr-3 font-mono text-[12px] text-[#374151]">{row.regulation_label}</td>
                        <td className="py-3.5 pr-5">
                          <StatusPill label={row.status_label} tone={row.status_tone} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <CollegeAdminPanelEmptyState
                iconSlug="graduation-cap"
                title="No programmes found"
                description={
                  debouncedSearch || levelFilter || departmentId || regulationFilter || statusFilter
                    ? "Try adjusting search or filters, or add a new programme with the guided wizard."
                    : "Add your first degree programme with department, regulation, duration, intake, and entry rules in a step-by-step flow."
                }
                action={
                  <CollegeAdminPrimaryLink href={createHref}>
                    <CollegeAdminPlusActionLabel iconClassName="size-3.5" label={data.add_programme_label } />
                  </CollegeAdminPrimaryLink>
                }
              />
            )}
          </CollegeAdminTablePanel>
        ) : null}
      </QueryState>
    </div>
  );
}

function Pagination({
  data,
  page,
  setPage,
}: {
  data: NonNullable<ReturnType<typeof useProgrammeManagementPage>["data"]>;
  page: number;
  setPage: (n: number) => void;
}) {
  return (
    <div className="flex items-center gap-1">
      <button
        type="button"
        className="rounded border border-[#dce3ec] px-2 py-1 disabled:opacity-40"
        disabled={!data.pagination.has_previous}
        onClick={() => setPage(Math.max(1, page - 1))}
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
              "min-w-8 rounded border px-2 py-1 tabular-nums text-xs font-semibold",
              num === data.pagination.page ? "border-[#245dd8] bg-[#eff6ff] text-[#245dd8]" : "border-[#dce3ec]",
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
        onClick={() => setPage(page + 1)}
      >
        ›
      </button>
    </div>
  );
}