"use client";

import { CollegeAdminModulePageLayout } from "@/features/college-admin/components/layout/college-admin-module-page-layout";
import { useCallback, useEffect, useState } from "react";

import { CalendarIcon } from "@/components/icons/erp/generated/calendar";
import { FilterIcon } from "@/components/icons/erp/generated/filter";
import { Button } from "@/components/ui/button";
import { CollegeAdminDownload } from "@/features/college-admin/components/layout/college-admin-erp-icons";
import {
  CollegeAdminKpiGrid,
  CollegeAdminUserDashboardKpiCard,
} from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useStudentAttendanceOverviewPage } from "@/features/college-admin/hooks/use-student-attendance-overview";
import type { StudentAttendanceDistributionBar } from "@/features/college-admin/types/student-attendance-overview";
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

function DistributionBars({ bars }: { bars: StudentAttendanceDistributionBar[] }) {
  if (!bars.length) {
    return <p className="text-sm text-[#9ca3af]">No attendance distribution for this term yet.</p>;
  }
  const toneColor: Record<string, string> = {
    success: "bg-[#10b981]",
    info: "bg-[#245dd8]",
    error: "bg-[#ef4444]",
  };
  return (
    <ul className="space-y-4">
      {bars.map((bar) => (
        <li key={bar.bucket_key}>
          <div className="mb-1.5 flex items-center justify-between text-[12px]">
            <span className="font-medium text-[#374151]">{bar.label}</span>
            <span className="tabular-nums text-[#111827]">{bar.student_count.toLocaleString("en-IN")}</span>
          </div>
          <div className="h-2.5 overflow-hidden rounded-full bg-[#eef2f7]">
            <div
              className={cn("h-full rounded-full", toneColor[bar.bar_tone] ?? "bg-[#245dd8]")}
              style={{ width: `${Math.max(4, bar.share_pct)}%` }}
            />
          </div>
        </li>
      ))}
    </ul>
  );
}

export function StudentAttendanceOverviewDashboard() {
  const [termKey, setTermKey] = useState("");
  const [programmeCode, setProgrammeCode] = useState("");

  const queryParams = {
    term_key: termKey || undefined,
    programme_code: programmeCode || undefined,
  };

  const { data, isLoading, isError, error, refetch } = useStudentAttendanceOverviewPage(queryParams);

  useEffect(() => {
    if (data?.selected_term_key && !termKey) {
      setTermKey(data.selected_term_key);
    }
  }, [data?.selected_term_key, termKey]);

  const handleExport = useCallback(() => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `student-attendance-overview-${new Date(data.generated_at).toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data]);

  return (
    <CollegeAdminModulePageLayout figmaFrame="159:7247">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Student Attendance Overview"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">{data?.page_subtitle ?? "Across programmes and semesters"}</p>
        </div>
        <Button
          type="button"
          variant="outline"
          className="h-9 shrink-0 gap-1.5 border-[#dce3ec] text-xs font-medium text-[#374151]"
          onClick={handleExport}
          disabled={isLoading || !data}
        >
          <CollegeAdminDownload className="size-3.5" />
          {data?.export_label ?? "Export"}
        </Button>
      </div>

      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-wrap items-center gap-2">
          <FilterSelect
            icon={<CalendarIcon className="size-3.5" aria-hidden />}
            label={data?.term_filter_label ?? "Academic term"}
            value={termKey}
            onChange={setTermKey}
            options={data?.term_options ?? []}
          />
          <FilterSelect
            icon={<FilterIcon className="size-3.5" aria-hidden />}
            label={data?.programme_filter_label ?? "Programme"}
            value={programmeCode}
            onChange={setProgrammeCode}
            options={data?.programme_options ?? [{ value: "", label: "All programmes" }]}
          />
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

            <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_320px]">
              <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                  <h3 className="text-[14px] font-semibold text-[#111827]">{data.programme_table_title}</h3>
                </div>
                {data.programme_rows.length ? (
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[32rem] text-left text-[13px]">
                      <thead>
                        <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                          {data.programme_table_headers.map((header, index) => (
                            <th
                              key={header}
                              className={cn(
                                "pb-3 font-medium",
                                index === 0 ? "px-5" : "pr-3 text-right",
                              )}
                            >
                              {header}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#f1f5f9]">
                        {data.programme_rows.map((row) => (
                          <tr key={row.programme_code} className="hover:bg-[#f9fafb]">
                            <td className="px-5 py-3 font-medium text-[#111827]">{row.programme_label}</td>
                            <td className="py-3 pr-3 text-right tabular-nums text-[#374151]">
                              {row.student_count.toLocaleString("en-IN")}
                            </td>
                            <td className="py-3 pr-3 text-right tabular-nums text-[#374151]">
                              {row.average_pct != null ? `${row.average_pct}%` : "—"}
                            </td>
                            <td className="py-3 pr-5 text-right tabular-nums text-[#374151]">
                              {row.below_minimum_count.toLocaleString("en-IN")}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="px-5 py-10 text-center text-sm text-[#9ca3af]">
                    No programme attendance data for the current filters.
                  </p>
                )}
                <div className="border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
                  {data.programme_table_footer_label}
                </div>
              </section>

              <section className="h-fit rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <h3 className="mb-4 text-[14px] font-semibold text-[#111827]">{data.distribution_title}</h3>
                <DistributionBars bars={data.distribution_bars} />
              </section>
            </div>

          </>
        ) : null}
      </QueryState>
    </CollegeAdminModulePageLayout>
  );
}