"use client";

import { onCollegeAdminMutationError } from "@/features/college-admin/context/college-admin-validation-context";
import { toast } from "sonner";

import { RefreshCwIcon } from "@/components/icons/erp/generated/refresh-cw";
import { Button } from "@/components/ui/button";
import { ExaminationRegistrationSubNav } from "@/features/college-admin/components/examinations/examination-registration-sub-nav";
import {
  CollegeAdminKpiGrid,
  CollegeAdminUserDashboardKpiCard,
} from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useProcessResults, useResultProcessingPage } from "@/features/college-admin/hooks/use-result-processing";
import { cn } from "@/lib/utils";


export function ResultProcessingDashboard() {
  const { data, isLoading, isError, error, refetch } = useResultProcessingPage();
  const process = useProcessResults();

  const handleProcess = () => {
    if (!data?.selected_session_id) return;
    process.mutate(
      { session_id: data.selected_session_id },
      {
        onSuccess: () => toast.success("Results processed."),
        onError: onCollegeAdminMutationError,
      },
    );
  };

  return (
    <div className="space-y-5" data-figma-frame="CA-09-result-processing">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">{data?.page_title ?? "Result Processing"}</h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">{data?.page_subtitle ?? "Process results for the active session"}</p>
        </div>
        <Button
          type="button"
          className="h-9 gap-1.5 bg-[#245dd8] text-xs font-medium hover:bg-[#1f4fb8]"
          disabled={process.isPending || !data?.selected_session_id}
          onClick={handleProcess}
        >
          <RefreshCwIcon className="size-3.5" aria-hidden />
          {data?.process_label ?? "Process"}
        </Button>
      </div>

      {data?.sub_nav?.length ? <ExaminationRegistrationSubNav items={data.sub_nav} /> : null}

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            <CollegeAdminKpiGrid>
              {data.kpis.map((kpi, index) => (
                <CollegeAdminUserDashboardKpiCard key={kpi.key} kpi={kpi} index={index} />
              ))}
            </CollegeAdminKpiGrid>

            <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white px-5 py-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <h3 className="mb-5 text-[14px] font-semibold text-[#111827]">{data.pass_chart_section_title}</h3>
              {data.pass_by_programme.length ? (
                <ul className="space-y-4">
                  {data.pass_by_programme.map((row) => (
                    <li key={row.programme_code} className="grid grid-cols-1 items-center gap-2 sm:grid-cols-[minmax(10rem,14rem)_1fr_auto] sm:gap-4">
                      <span className="text-[13px] font-medium text-[#111827]">{row.programme_label}</span>
                      <div className="h-2 overflow-hidden rounded-full bg-[#f1f5f9]">
                        <div
                          className={cn("h-full rounded-full transition-all", row.bar_tone === "success" ? "bg-[#10b981]" : "bg-[#245dd8]")}
                          style={{ width: `${Math.min(100, Math.max(0, row.pass_percent))}%` }}
                        />
                      </div>
                      <span className="text-[13px] tabular-nums text-[#374151] sm:text-right">{row.pass_percent_label}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="py-6 text-center text-sm text-[#9ca3af]">No programme results to display yet.</p>
              )}
            </section>

          </>
        ) : null}
      </QueryState>
    </div>
  );
}