"use client";

import { CollegeAdminModulePageLayout } from "@/features/college-admin/components/layout/college-admin-module-page-layout";
import { useCallback, useEffect, useState } from "react";

import { CalendarIcon } from "@/components/icons/erp/generated/calendar";
import { FilterIcon } from "@/components/icons/erp/generated/filter";
import { Button } from "@/components/ui/button";
import { CollegeAdminDownload } from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useSubjectWiseAttendancePage } from "@/features/college-admin/hooks/use-subject-wise-attendance";
import { cn } from "@/lib/utils";

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
    <div className="relative">
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

export function SubjectWiseAttendanceDashboard() {
  const [termKey, setTermKey] = useState("");
  const [scopeKey, setScopeKey] = useState("");

  const queryParams = {
    term_key: termKey || undefined,
    scope_key: scopeKey || undefined,
  };

  const { data, isLoading, isError, error, refetch } = useSubjectWiseAttendancePage(queryParams);

  useEffect(() => {
    if (data?.selected_term_key && !termKey) setTermKey(data.selected_term_key);
  }, [data?.selected_term_key, termKey]);

  const handleExport = useCallback(() => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `subject-wise-attendance-${new Date(data.generated_at).toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data]);

  return (
    <CollegeAdminModulePageLayout figmaFrame="159:7922">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Subject-wise Attendance"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">{data?.page_subtitle ?? "Class attendance by subject"}</p>
        </div>
        <Button
          type="button"
          variant="outline"
          className="h-9 gap-1.5 border-[#dce3ec] text-xs font-medium"
          onClick={handleExport}
          disabled={isLoading || !data}
        >
          <CollegeAdminDownload className="size-3.5" />
          {data?.export_label ?? "Export"}
        </Button>
      </div>

      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-wrap gap-2">
          <FilterSelect
            icon={<CalendarIcon className="size-3.5" aria-hidden />}
            label={data?.term_filter_label ?? "Academic term"}
            value={termKey}
            onChange={setTermKey}
            options={data?.term_options ?? []}
          />
          <FilterSelect
            icon={<FilterIcon className="size-3.5" aria-hidden />}
            label={data?.scope_filter_label ?? "Programme scope"}
            value={scopeKey}
            onChange={setScopeKey}
            options={data?.scope_options ?? [{ value: "", label: "All scopes" }]}
          />
        </div>
        <div className="flex items-center gap-3 text-[12px] text-[#6b7280]">
        </div>
      </div>

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.subjects_table_title}</h3>
              </div>
              {data.subject_rows.length ? (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[44rem] text-left text-[13px]">
                    <thead>
                      <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                        {data.subjects_table_headers.map((header, index) => (
                          <th
                            key={header}
                            className={cn(
                              "pb-3 font-medium",
                              index === 0 ? "px-5" : "pr-3",
                              index >= 3 && "text-right",
                            )}
                          >
                            {header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#f1f5f9]">
                      {data.subject_rows.map((row) => (
                        <tr key={row.subject_code} className="hover:bg-[#f9fafb]">
                          <td className="px-5 py-3 font-medium text-[#111827]">{row.subject_name}</td>
                          <td className="py-3 pr-3 tabular-nums text-[#374151]">{row.subject_code}</td>
                          <td className="py-3 pr-3 text-[#374151]">{row.faculty_label}</td>
                          <td className="py-3 pr-3 text-right tabular-nums">{row.classes_held}</td>
                          <td className="py-3 pr-3 text-right tabular-nums">
                            {row.average_pct != null ? `${row.average_pct}%` : "—"}
                          </td>
                          <td className="py-3 pr-5 text-right tabular-nums">{row.below_minimum_count}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="px-5 py-10 text-center text-sm text-[#9ca3af]">No subject attendance for these filters.</p>
              )}
              <div className="border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
                {data.subjects_footer_label}
              </div>
            </section>

          </>
        ) : null}
      </QueryState>
    </CollegeAdminModulePageLayout>
  );
}