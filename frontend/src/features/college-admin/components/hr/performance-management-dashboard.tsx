"use client";

import { useMemo } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { CollegeAdminChevronRight } from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { HrRecruitmentSubNav } from "@/features/college-admin/components/hr/hr-recruitment-sub-nav";
import {
  CollegeAdminKpiGrid,
  CollegeAdminUserDashboardKpiCard,
} from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { onCollegeAdminMutationError } from "@/features/college-admin/context/college-admin-validation-context";
import {
  useHrPerformanceManagementPage,
  useOpenHrPerformanceCycle,
} from "@/features/college-admin/hooks/use-hr-benefits-performance";
import type { HrPerformanceManagementPage, HrPerformanceProgressRow } from "@/features/college-admin/types/hr-benefits-performance";
import type { HrRecruitmentSubNavItem } from "@/features/college-admin/types/hr-recruitment";
import { cn } from "@/lib/utils";

const DEFAULT_SUB_NAV: HrRecruitmentSubNavItem[] = [
  { key: "benefits-claims", label: "Employee benefits & claims", href: "/college-admin/hr/employee-benefits-claims" },
  { key: "performance", label: "Performance management", href: "/college-admin/hr/performance-management" },
];

const PLACEHOLDER_KPIS = [
  { key: "self_reviews", label: "Self reviews done", value: "0", hint_line: "of 0", hint_tone: "neutral" },
  { key: "manager_reviews", label: "Manager reviews done", value: "0", hint_line: "Pending", hint_tone: "neutral" },
  { key: "calibration_pending", label: "Calibration pending", value: "0", hint_line: "HR review", hint_tone: "neutral" },
  { key: "training_enrolled", label: "Training enrolled", value: "0", hint_line: "Active enrollments", hint_tone: "neutral" },
];

const DEFAULT_PROGRESS: HrPerformanceProgressRow[] = [
  { key: "self_review", label: "Self review", completed_count: 0, total_count: 0, progress_pct: 0, tone: "info" },
  { key: "manager_review", label: "Manager review", completed_count: 0, total_count: 0, progress_pct: 0, tone: "info" },
  { key: "calibration", label: "Calibration", completed_count: 0, total_count: 0, progress_pct: 0, tone: "warning" },
];

function ProgressBar({ row }: { row: HrPerformanceProgressRow }) {
  const pct = Math.min(100, Math.max(0, row.progress_pct));
  const barColor = row.tone === "warning" ? "bg-[#d97706]" : "bg-[#245dd8]";
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-2 text-[13px]">
        <span className="font-medium text-[#111827]">{row.label}</span>
        <span className="tabular-nums text-[#6b7280]">
          {row.completed_count.toLocaleString("en-IN")} of {row.total_count.toLocaleString("en-IN")}
        </span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-[#f3f4f6]">
        <div className={cn("h-full rounded-full transition-all", barColor)} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function mergeView(data: HrPerformanceManagementPage | undefined) {
  return {
    page_title: data?.page_title ?? "Performance Management",
    page_subtitle: data?.page_subtitle ?? "Appraisal cycle",
    open_cycle_label: data?.open_cycle_label ?? "Open cycle",
    can_open_cycle: data?.can_open_cycle ?? true,
    open_cycle_blocked_message: data?.open_cycle_blocked_message ?? null,
    selected_cycle_id: data?.selected_cycle_id ?? undefined,
    sub_nav: data?.sub_nav?.length ? data.sub_nav : DEFAULT_SUB_NAV,
    kpis: data?.kpis?.length ? data.kpis : PLACEHOLDER_KPIS,
    progress_section_title: data?.progress_section_title ?? "Appraisal progress",
    progress_rows: data?.progress_rows?.length ? data.progress_rows : DEFAULT_PROGRESS,
    footer_disclaimer: data?.footer_disclaimer ?? "",
    footer_snapshot_label: data?.footer_snapshot_label ?? "",
  };
}

export function PerformanceManagementDashboard() {
  const { data, isLoading, isError, error, refetch, isFetching } = useHrPerformanceManagementPage();
  const view = useMemo(() => mergeView(data), [data]);

  const openCycle = useOpenHrPerformanceCycle(view.selected_cycle_id);

  const onOpenCycle = () => {
    openCycle.mutate(undefined, {
      onSuccess: (res) => {
        if (res.already_active) {
          toast.message("Cycle already active");
        } else {
          toast.success(
            res.reviews_created != null
              ? `Cycle opened · ${res.reviews_created.toLocaleString("en-IN")} review(s) created`
              : "Appraisal cycle opened",
          );
        }
      },
      onError: onCollegeAdminMutationError,
    });
  };

  return (
    <div className="space-y-5" data-figma-frame="160:10718">
      <HrRecruitmentSubNav items={view.sub_nav} />

      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">{view.page_title}</h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">{view.page_subtitle}</p>
        </div>
        <Button
          type="button"
          className="h-9 shrink-0 gap-1.5 bg-[#245dd8] text-xs text-white hover:bg-[#1f4fb8]"
          disabled={!view.can_open_cycle || openCycle.isPending}
          onClick={onOpenCycle}
        >
          {view.open_cycle_label}
          <CollegeAdminChevronRight className="size-3.5" aria-hidden />
        </Button>
      </div>

      {view.open_cycle_blocked_message ? (
        <p className="rounded-lg border border-[#fef3c7] bg-[#fffbeb] px-4 py-3 text-[13px] text-[#92400e]">
          {view.open_cycle_blocked_message}
        </p>
      ) : null}

      {isLoading || isFetching ? (
        <p className="text-[12px] text-[#9ca3af]">{isLoading ? "Loading performance data…" : "Updating…"}</p>
      ) : null}

      {isError ? <QueryState isError={isError} error={error} onRetry={() => void refetch()} /> : null}

      {!isError ? (
        <>
          <CollegeAdminKpiGrid>
            {view.kpis.map((kpi, index) => (
              <CollegeAdminUserDashboardKpiCard key={kpi.key} kpi={kpi} index={index} />
            ))}
          </CollegeAdminKpiGrid>

          <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
            <h3 className="mb-5 text-[14px] font-semibold text-[#111827]">{view.progress_section_title}</h3>
            <div className="space-y-5">
              {view.progress_rows.map((row) => (
                <ProgressBar key={row.key} row={row} />
              ))}
            </div>
          </section>

          <footer className="flex flex-col gap-1 text-[11px] text-[#9ca3af] sm:flex-row sm:items-center sm:justify-between">
            <p>{view.footer_disclaimer}</p>
            {view.footer_snapshot_label ? <p>{view.footer_snapshot_label}</p> : null}
          </footer>
        </>
      ) : null}
    </div>
  );
}