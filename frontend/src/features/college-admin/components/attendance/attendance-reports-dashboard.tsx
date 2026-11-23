"use client";

import { useState } from "react";
import { onCollegeAdminMutationError } from "@/features/college-admin/context/college-admin-validation-context";
import { toast } from "sonner";

import { PlusIcon } from "@/components/icons/erp/generated/plus";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useAttendanceReportsPage,
  useCreateAttendanceReport,
} from "@/features/college-admin/hooks/use-attendance-reports";

export function AttendanceReportsDashboard() {
  const [page, setPage] = useState(1);
  const queryParams = { page, page_size: 4 };
  const { data, isLoading, isError, error, refetch } = useAttendanceReportsPage(queryParams);
  const createReport = useCreateAttendanceReport(queryParams);

  const [showCreate, setShowCreate] = useState(false);
  const [templateKey, setTemplateKey] = useState("");

  const handleCreate = () => {
    if (!templateKey) {
      toast.error("Select a report type");
      return;
    }
    createReport.mutate(
      { template_key: templateKey },
      {
        onSuccess: () => {
          toast.success("Report created");
          setShowCreate(false);
          setTemplateKey("");
        },
        onError: onCollegeAdminMutationError,
      },
    );
  };

  return (
    <div className="space-y-5" data-figma-frame="159:10420">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Attendance Reports"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">{data?.page_subtitle ?? "—"}</p>
        </div>
        <Button
          type="button"
          className="h-9 shrink-0 gap-1.5 bg-[#245dd8] text-xs font-medium text-white hover:bg-[#1f4fb8]"
          onClick={() => setShowCreate((v) => !v)}
        >
          <PlusIcon className="size-3.5" aria-hidden />
          {data?.create_report_label ?? "Create report"}
        </Button>
      </div>

      {showCreate && data ? (
        <section className="flex flex-col gap-3 rounded-xl border border-[#e8ecf2] bg-white p-4 shadow-[0_1px_2px_rgba(15,23,42,0.04)] sm:flex-row sm:items-end">
          <div className="min-w-[16rem] flex-1 space-y-1.5">
            <Label className="text-[13px] text-[#374151]">Report type</Label>
            <select
              value={templateKey}
              onChange={(e) => setTemplateKey(e.target.value)}
              className="h-9 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px] text-[#374151]"
            >
              <option value="">Select…</option>
              {data.create_report_templates.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
          <Button
            type="button"
            className="h-9 bg-[#245dd8] text-xs hover:bg-[#1f4fb8]"
            disabled={createReport.isPending}
            onClick={handleCreate}
          >
            Create
          </Button>
        </section>
      ) : null}

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.reports_section_title}</h3>
              </div>
              {data.report_rows.length ? (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[44rem] text-left text-[13px]">
                    <thead>
                      <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                        {data.reports_table_headers.map((header) => (
                          <th key={header} className="px-5 py-3 font-medium">
                            {header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#f1f5f9]">
                      {data.report_rows.map((row) => (
                        <tr key={row.row_key} className="text-[#111827]">
                          <td className="px-5 py-3.5 font-semibold">{row.report_title}</td>
                          <td className="px-5 py-3.5 text-[#6b7280]">{row.period_label}</td>
                          <td className="px-5 py-3.5">{row.format_label}</td>
                          <td className="px-5 py-3.5 text-[#6b7280] tabular-nums">{row.last_run_label}</td>
                          <td className="px-5 py-3.5 text-[#6b7280]">{row.schedule_label}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="px-5 py-8 text-center text-[13px] text-[#6b7280]">No reports configured.</p>
              )}
              <div className="flex items-center justify-between border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
                <span>{data.reports_table_footer_label}</span>
                <div className="flex gap-2">
                  <button
                    type="button"
                    disabled={page <= 1}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    className="rounded px-2 py-0.5 hover:bg-[#f3f4f6] disabled:opacity-40"
                  >
                    Prev
                  </button>
                  <button
                    type="button"
                    onClick={() => setPage((p) => p + 1)}
                    className="rounded px-2 py-0.5 hover:bg-[#f3f4f6]"
                  >
                    Next
                  </button>
                </div>
              </div>
            </section>

          </>
        ) : null}
      </QueryState>
    </div>
  );
}