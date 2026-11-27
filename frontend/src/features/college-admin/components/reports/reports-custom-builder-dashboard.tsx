"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

import { ChevronRightIcon } from "@/components/icons/erp/generated/chevron-right";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { CollegeAdminDownload } from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { onCollegeAdminMutationError } from "@/features/college-admin/context/college-admin-validation-context";
import {
  useReportsCustomBuilderPage,
  useRunReportsGenerate,
  useSaveReportsCustomBuilder,
} from "@/features/college-admin/hooks/use-reports-custom-scheduled";
import { cn } from "@/lib/utils";

function StepCircle({ number, status }: { number: number; status: string }) {
  const done = status === "done";
  const active = status === "active";
  return (
    <div
      className={cn(
        "flex h-8 w-8 items-center justify-center rounded-full text-[12px] font-semibold",
        done || active ? "bg-[#245dd8] text-white" : "border border-[#dce3ec] bg-white text-[#9ca3af]",
      )}
    >
      {done ? "✓" : number}
    </div>
  );
}

export function ReportsCustomBuilderDashboard() {
  const [dataSource, setDataSource] = useState("");
  const [selectedFields, setSelectedFields] = useState<string[]>([]);
  const [groupBy, setGroupBy] = useState("");
  const [sortBy, setSortBy] = useState("");
  const [format, setFormat] = useState("excel");
  const [dateRange, setDateRange] = useState("");

  const queryParams = useMemo(
    () => ({ data_source: dataSource || undefined, active_step: "filters" }),
    [dataSource],
  );
  const { data, isLoading, isError, error, refetch, isFetching } = useReportsCustomBuilderPage(queryParams);
  const saveTemplate = useSaveReportsCustomBuilder(queryParams);
  const runReport = useRunReportsGenerate();

  useEffect(() => {
    if (!data) return;
    setDataSource(data.selected_data_source);
    setSelectedFields(data.selected_fields);
    setGroupBy(data.selected_group_by);
    setSortBy(data.selected_sort_by);
    setFormat(data.selected_format);
    setDateRange(data.selected_date_range);
  }, [data]);

  const toggleField = useCallback((field: string) => {
    setSelectedFields((prev) =>
      prev.includes(field) ? prev.filter((f) => f !== field) : [...prev, field],
    );
  }, []);

  const handleSave = () => {
    if (!data) return;
    saveTemplate.mutate(
      {
        filter_id: data.filter_id,
        data_source: dataSource || data.selected_data_source,
        selected_fields: selectedFields,
        group_by: groupBy,
        sort_by: sortBy,
        export_format: format,
        academic_year: dateRange || undefined,
      },
      {
        onSuccess: () => toast.success("Template saved"),
        onError: onCollegeAdminMutationError,
      },
    );
  };

  const handleRun = () => {
    if (!data?.report_key) return;
    runReport.mutate(data.report_key, {
      onSuccess: () => toast.success("Report run queued"),
      onError: onCollegeAdminMutationError,
    });
  };

  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Custom Report Builder"}
          </h2>
          {data?.page_subtitle ? <p className="mt-1 text-[14px] text-[#6b7280]">{data.page_subtitle}</p> : null}
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            type="button"
            variant="outline"
            className="h-9 gap-1.5 border-[#dce3ec] text-xs"
            disabled={saveTemplate.isPending}
            onClick={handleSave}
          >
            <CollegeAdminDownload className="h-4 w-4" />
            {data?.save_template_label ?? "Save template"}
          </Button>
          <Button
            type="button"
            className="h-9 gap-1 bg-[#245dd8] text-xs text-white hover:bg-[#1f4fb8]"
            disabled={runReport.isPending}
            onClick={handleRun}
          >
            {data?.run_label ?? "Run"}
            <ChevronRightIcon className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {data?.steps?.length ? (
        <div className="flex flex-wrap items-center gap-2 text-[12px] text-[#6b7280]">
          {data.steps.map((step, index) => (
            <div key={step.step_key} className="flex items-center gap-2">
              <StepCircle number={step.step_number} status={step.status} />
              <span className={cn(step.status === "active" && "font-medium text-[#111827]")}>{step.step_label}</span>
              {index < data.steps.length - 1 ? <span className="mx-1 hidden h-px w-6 bg-[#e5e7eb] sm:block" /> : null}
            </div>
          ))}
        </div>
      ) : null}

      {isLoading || isFetching ? (
        <p className="text-[12px] text-[#9ca3af]">{isLoading ? "Loading builder…" : "Updating…"}</p>
      ) : null}

      <QueryState isError={isError} error={error} onRetry={() => void refetch()}>
        <div className="grid gap-5 lg:grid-cols-5">
          <section className="space-y-4 rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)] lg:col-span-3">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1.5 sm:col-span-2">
                <Label className="text-[13px]">{data?.data_source_label ?? "Data source"}</Label>
                <select
                  value={dataSource}
                  onChange={(e) => setDataSource(e.target.value)}
                  className="h-9 w-full rounded-md border border-[#dce3ec] px-3 text-[13px]"
                >
                  {(data?.data_source_options ?? []).map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-1.5 sm:col-span-2">
                <Label className="text-[13px]">{data?.fields_label ?? "Fields"}</Label>
                <div className="flex min-h-[2.5rem] flex-wrap gap-1.5 rounded-md border border-[#dce3ec] p-2">
                  {(data?.field_options ?? []).map((opt) => {
                    const on = selectedFields.includes(opt.value);
                    return (
                      <button
                        key={opt.value}
                        type="button"
                        onClick={() => toggleField(opt.value)}
                        className={cn(
                          "rounded-full px-2.5 py-0.5 text-[12px]",
                          on ? "bg-[#eff6ff] text-[#1d4ed8]" : "bg-[#f3f4f6] text-[#6b7280]",
                        )}
                      >
                        {opt.label}
                        {on ? " ×" : ""}
                      </button>
                    );
                  })}
                </div>
              </div>
              <div className="space-y-1.5">
                <Label className="text-[13px]">{data?.group_by_label ?? "Group by"}</Label>
                <select
                  value={groupBy}
                  onChange={(e) => setGroupBy(e.target.value)}
                  className="h-9 w-full rounded-md border border-[#dce3ec] px-3 text-[13px]"
                >
                  {(data?.group_by_options ?? []).map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-1.5">
                <Label className="text-[13px]">{data?.sort_by_label ?? "Sort by"}</Label>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="h-9 w-full rounded-md border border-[#dce3ec] px-3 text-[13px]"
                >
                  {(data?.sort_by_options ?? []).map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-1.5">
                <Label className="text-[13px]">{data?.date_range_label ?? "Date range"}</Label>
                <select
                  value={dateRange}
                  onChange={(e) => setDateRange(e.target.value)}
                  className="h-9 w-full rounded-md border border-[#dce3ec] px-3 text-[13px]"
                >
                  {(data?.date_range_options ?? []).map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-1.5">
                <Label className="text-[13px]">{data?.format_label ?? "Format"}</Label>
                <select
                  value={format}
                  onChange={(e) => setFormat(e.target.value)}
                  className="h-9 w-full rounded-md border border-[#dce3ec] px-3 text-[13px]"
                >
                  {(data?.format_options ?? []).map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </section>

          <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)] lg:col-span-2">
            <div className="border-b border-[#f1f5f9] px-5 py-3.5">
              <h3 className="text-[14px] font-semibold text-[#111827]">
                {data?.preview_section_title ?? "Preview"}
              </h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-[13px]">
                <thead>
                  <tr className="border-b border-[#f1f5f9] text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                    {(data?.preview_headers ?? []).map((h) => (
                      <th key={h} className="px-5 py-3 font-medium">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#f1f5f9]">
                  {data?.preview_rows?.length ? (
                    data.preview_rows.map((row) => (
                      <tr key={row.row_key}>
                        <td className="px-5 py-2.5 font-medium text-[#111827]">{row.name_label}</td>
                        <td className="px-5 py-2.5 text-[#6b7280]">{row.programme_label}</td>
                        <td className="px-5 py-2.5 tabular-nums text-[#6b7280]">{row.attendance_label}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={3} className="px-5 py-8 text-center text-sm text-[#9ca3af]">
                        {data?.empty_preview_message ?? "No preview data."}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      </QueryState>
    </div>
  );
}