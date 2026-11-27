"use client";

import { CollegeAdminModulePageLayout } from "@/features/college-admin/components/layout/college-admin-module-page-layout";
import Link from "next/link";

import { PencilIcon } from "@/components/icons/erp/generated/pencil";
import {
  CollegeAdminKpiGrid,
  CollegeAdminUserDashboardKpiCard,
} from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useHostelMessManagementPage } from "@/features/college-admin/hooks/use-hostel-mess-management";
import { cn } from "@/lib/utils";

const BAR_TONE: Record<string, string> = {
  info: "bg-[#3b82f6]",
  success: "bg-[#10b981]",
  warning: "bg-[#f59e0b]",
  muted: "bg-[#9ca3af]",
};

export function HostelMessManagementDashboard() {
  const { data, isLoading, isError, error, refetch, isFetching } = useHostelMessManagementPage();

  const menuHeaders = data?.menu_table_headers ?? [];
  const feedbackDimensions = data?.feedback_dimensions ?? [];
  const kpis = data?.kpis ?? [];

  return (
    <CollegeAdminModulePageLayout figmaFrame="161:4839">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Mess Management"}
          </h2>
          {data?.page_subtitle ? (
            <p className="mt-1 text-[14px] text-[#6b7280]">{data.page_subtitle}</p>
          ) : null}
        </div>
        <Link
          href={data?.edit_menu_href ?? "#"}
          className="inline-flex h-9 shrink-0 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
        >
          <PencilIcon className="size-3.5" aria-hidden />
          {data?.edit_menu_label ?? "Edit menu"}
        </Link>
      </div>

      {isLoading || isFetching ? (
        <p className="text-[12px] text-[#9ca3af]">{isLoading ? "Loading mess data…" : "Updating…"}</p>
      ) : null}

      <QueryState
        isLoading={isLoading && !data}
        isError={isError}
        error={error}
        onRetry={() => void refetch()}
      >
        <>
          <CollegeAdminKpiGrid>
            {kpis.map((kpi, index) => (
              <CollegeAdminUserDashboardKpiCard key={kpi.key} kpi={kpi} index={index} />
            ))}
          </CollegeAdminKpiGrid>

          <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_300px]">
            <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                <h3 className="text-[14px] font-semibold text-[#111827]">
                  {data?.menu_section_title ?? "Today's menu"}
                </h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[28rem] text-left text-[13px]">
                  <thead>
                    <tr className="border-b border-[#f1f5f9] text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                      {menuHeaders.map((header, index, headers) => (
                        <th
                          key={header}
                          className={cn(
                            "pb-3 pt-4 font-medium",
                            index === 0 ? "pl-5 pr-3" : "pr-3",
                            index === headers.length - 1 ? "pr-5 text-right tabular-nums" : "",
                          )}
                        >
                          {header}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#f1f5f9]">
                    {data?.menu_rows.length ? (
                      data.menu_rows.map((row) => (
                        <tr key={row.meal_key} className="text-[#374151]">
                          <td className="pl-5 py-3 pr-3 font-semibold text-[#111827]">{row.meal_label}</td>
                          <td className="py-3 pr-3 text-[#6b7280]">{row.menu_label}</td>
                          <td className="py-3 pr-5 text-right tabular-nums">{row.served_label}</td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td
                          colSpan={Math.max(menuHeaders.length, 1)}
                          className="px-5 py-10 text-center text-[13px] text-[#6b7280]"
                        >
                          {data?.empty_menu_message ?? "No menu published for today."}
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <h3 className="text-[14px] font-semibold text-[#111827]">
                {data?.feedback_section_title ?? "Feedback"}
              </h3>
              <div className="mt-4 space-y-5">
                {feedbackDimensions.length ? (
                  feedbackDimensions.map((dim) => (
                    <div key={dim.key}>
                      <div className="mb-1.5 flex items-center justify-between gap-2">
                        <span className="text-[13px] font-medium text-[#374151]">{dim.label}</span>
                        <span className="text-[12px] font-semibold tabular-nums text-[#111827]">
                          {dim.score_label}
                        </span>
                      </div>
                      <div className="h-2 overflow-hidden rounded-full bg-[#f1f5f9]">
                        <div
                          className={cn("h-full rounded-full", BAR_TONE[dim.tone] ?? BAR_TONE.muted)}
                          style={{ width: `${Math.min(100, Math.max(0, dim.progress_percent))}%` }}
                        />
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-[13px] text-[#9ca3af]">No feedback scores recorded yet.</p>
                )}
              </div>
            </section>
          </div>
        </>
      </QueryState>
    </CollegeAdminModulePageLayout>
  );
}