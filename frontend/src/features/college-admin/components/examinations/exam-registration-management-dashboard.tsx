"use client";

import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";

import { SearchIcon } from "@/components/icons/erp/generated/search";
import { Button } from "@/components/ui/button";
import { CollegeAdminDownload } from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { ExaminationRegistrationSubNav } from "@/features/college-admin/components/examinations/examination-registration-sub-nav";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useExamRegistrationManagementPage } from "@/features/college-admin/hooks/use-exam-registration-management";
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
      className="h-9 min-w-[9rem] max-w-[18rem] rounded-md border border-[#dce3ec] bg-white pl-3 pr-8 text-[13px] text-[#374151]"
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


export function ExamRegistrationManagementDashboard() {
  const [page, setPage] = useState(1);
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [programme, setProgramme] = useState("");

  useEffect(() => {
    const handle = window.setTimeout(() => setSearch(searchInput.trim()), 300);
    return () => window.clearTimeout(handle);
  }, [searchInput]);

  useEffect(() => {
    setPage(1);
  }, [status, programme, search]);

  const { data, isLoading, isError, error, refetch } = useExamRegistrationManagementPage({
    page,
    status: status || undefined,
    programme_code: programme || undefined,
    search: search || undefined,
  });

  const handleExport = useCallback(() => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `exam-registration-${new Date(data.generated_at).toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success("Registration export downloaded.");
  }, [data]);

  return (
    <div className="space-y-5" data-figma-frame="159:12120">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Exam Registration Management"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">
            {data?.page_subtitle ?? "Student registrations for the session"}
          </p>
        </div>
        <Button
          type="button"
          className="h-9 shrink-0 gap-1.5 bg-[#245dd8] text-xs font-medium hover:bg-[#1f4fb8]"
          onClick={handleExport}
          disabled={isLoading || !data}
        >
          <CollegeAdminDownload className="size-3.5" />
          {data?.export_label ?? "Export"}
        </Button>
      </div>

      {data?.sub_nav?.length ? <ExaminationRegistrationSubNav items={data.sub_nav} /> : null}

      <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
        <div className="relative min-w-[14rem] flex-1 sm:max-w-md">
          <SearchIcon className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-[#9ca3af]" aria-hidden />
          <input
            type="search"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder={data?.search_placeholder ?? "Search student or register number"}
            className="h-9 w-full rounded-md border border-[#dce3ec] bg-white pl-9 pr-3 text-[13px] text-[#374151] placeholder:text-[#9ca3af]"
          />
        </div>
        <FilterSelect
          label={data?.programme_filter_label ?? "Programme"}
          value={programme}
          onChange={setProgramme}
          options={data?.programme_options ?? [{ value: "", label: "All programmes" }]}
        />
        <FilterSelect
          label={data?.status_filter_label ?? "Status"}
          value={status}
          onChange={setStatus}
          options={data?.status_options ?? [{ value: "", label: "All statuses" }]}
        />
      </div>

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.registrations_section_title}</h3>
              </div>
              {data.registration_rows.length ? (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[40rem] text-left text-[13px]">
                    <thead>
                      <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                        {data.table_headers.map((header, index) => (
                          <th
                            key={header}
                            className={cn(
                              "pb-3 font-medium",
                              index === 0 ? "pl-5 pr-3" : "pr-3",
                              index === data.table_headers.length - 1 ? "pr-5" : "",
                            )}
                          >
                            {header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#f1f5f9]">
                      {data.registration_rows.map((row) => (
                        <tr key={row.registration_id} className="text-[#374151]">
                          <td className="pl-5 py-3 pr-3 font-medium text-[#111827]">{row.student_name}</td>
                          <td className="py-3 pr-3 font-mono text-[12px] text-[#6b7280]">{row.register_number}</td>
                          <td className="py-3 pr-3 tabular-nums">{row.subjects_count}</td>
                          <td className="py-3 pr-3">
                            <StatusPill label={row.fee_status_label} tone={row.fee_status_tone} />
                          </td>
                          <td className="py-3 pr-3">
                            <StatusPill label={row.eligibility_status_label} tone={row.eligibility_status_tone} />
                          </td>
                          <td className="py-3 pr-5">
                            <StatusPill label={row.registration_status_label} tone={row.registration_status_tone} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="px-5 py-10 text-center text-sm text-[#9ca3af]">No registrations match your filters.</p>
              )}
              <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
                <span>{data.showing_label}</span>
                {data.pagination.total_pages > 0 ? (
                  <MotionPagination page={page} setPage={setPage} data={data} />
                ) : null}
              </div>
            </section>

          </>
        ) : null}
      </QueryState>
    </div>
  );
}

function MotionPagination({
  data,
  page,
  setPage,
}: {
  data: { pagination: { total_pages: number; page: number; page_numbers: number[]; has_previous: boolean; has_next: boolean } };
  page: number;
  setPage: (p: number) => void;
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
              "min-w-8 rounded border px-2 py-1 tabular-nums",
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