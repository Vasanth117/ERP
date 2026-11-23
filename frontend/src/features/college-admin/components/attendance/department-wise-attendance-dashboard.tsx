"use client";

import { useCallback, useEffect, useState } from "react";

import { CalendarIcon } from "@/components/icons/erp/generated/calendar";
import { Button } from "@/components/ui/button";
import { CollegeAdminDownload } from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useDepartmentWiseAttendancePage } from "@/features/college-admin/hooks/use-department-wise-attendance";
import type { AttendanceDashboardDepartmentRow } from "@/features/college-admin/types/attendance-dashboard";
import type { DepartmentWiseAttendanceBarItem } from "@/features/college-admin/types/department-wise-attendance";
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
    <div className="relative">
      <span className="pointer-events-none absolute left-3 top-1/2 z-[1] -translate-y-1/2 text-[#9ca3af]">
        <CalendarIcon className="size-3.5" aria-hidden />
      </span>
      <select
        aria-label={label}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="h-9 min-w-[9rem] rounded-md border border-[#dce3ec] bg-white pl-9 pr-8 text-[13px] text-[#374151]"
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

function DepartmentBars({ bars }: { bars: DepartmentWiseAttendanceBarItem[] }) {
  if (!bars.length) {
    return <p className="text-sm text-[#9ca3af]">No department averages yet.</p>;
  }
  const max = Math.max(...bars.map((b) => b.average_pct ?? 0), 1);
  return (
    <div className="flex items-end justify-between gap-3 px-1 pt-2">
      {bars.map((bar) => {
        const height = bar.average_pct != null ? Math.max(12, (bar.average_pct / max) * 100) : 12;
        return (
          <div key={bar.department_code} className="flex min-w-0 flex-1 flex-col items-center gap-2">
            <span className="text-[11px] font-medium tabular-nums text-[#111827]">
              {bar.average_pct != null ? `${bar.average_pct}%` : "—"}
            </span>
            <div
              className="w-full max-w-[3rem] rounded-t-md bg-[#245dd8]"
              style={{ height: `${height}px` }}
              role="presentation"
            />
            <span className="max-w-full truncate text-[10px] font-medium text-[#6b7280]">
              {bar.department_code}
            </span>
          </div>
        );
      })}
    </div>
  );
}

export function DepartmentWiseAttendanceDashboard() {
  const [termKey, setTermKey] = useState("");
  const queryParams = { term_key: termKey || undefined };
  const { data, isLoading, isError, error, refetch } = useDepartmentWiseAttendancePage(queryParams);

  useEffect(() => {
    if (data?.selected_term_key && !termKey) setTermKey(data.selected_term_key);
  }, [data?.selected_term_key, termKey]);

  const handleExport = useCallback(() => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `department-wise-attendance-${new Date(data.generated_at).toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data]);

  return (
    <div className="space-y-5" data-figma-frame="159:8235">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Department-wise Attendance"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">{data?.page_subtitle ?? "Compare departments"}</p>
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

      <div className="flex flex-wrap items-center justify-between gap-3">
        <FilterSelect
          label={data?.term_filter_label ?? "Academic term"}
          value={termKey}
          onChange={setTermKey}
          options={data?.term_options ?? []}
        />
        <div className="flex items-center gap-3 text-[12px] text-[#6b7280]">
        </div>
      </div>

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_280px]">
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
                            <td className="py-3 pr-3 text-right tabular-nums">{row.student_count.toLocaleString("en-IN")}</td>
                            <td className="py-3 pr-3 text-right tabular-nums">
                              {row.average_pct != null ? `${row.average_pct}%` : "—"}
                            </td>
                            <td className="py-3 pr-3 text-right tabular-nums">{row.below_minimum_count}</td>
                            <td className="py-3 pr-5">
                              <TrendPill row={row} />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="px-5 py-10 text-center text-sm text-[#9ca3af]">No department data for this term.</p>
                )}
                <div className="border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
                  {data.department_table_footer_label}
                </div>
              </section>

              <section className="h-fit rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <h3 className="mb-4 text-[14px] font-semibold text-[#111827]">{data.bars_section_title}</h3>
                <DepartmentBars bars={data.department_bars} />
              </section>
            </div>

          </>
        ) : null}
      </QueryState>
    </div>
  );
}