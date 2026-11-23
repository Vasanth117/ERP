"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";

import { CalendarIcon } from "@/components/icons/erp/generated/calendar";
import { CheckIcon } from "@/components/icons/erp/generated/check";
import { EyeIcon } from "@/components/icons/erp/generated/eye";
import { FilterIcon } from "@/components/icons/erp/generated/filter";
import { Button } from "@/components/ui/button";
import {
  CollegeAdminKpiGrid,
  CollegeAdminUserDashboardKpiCard,
} from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  usePreviewStudentPromotion,
  usePromoteEligibleStudents,
  useStudentPromotionManagementPage,
} from "@/features/college-admin/hooks/use-student-promotion-management";
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
          "h-9 min-w-[12rem] rounded-md border border-[#dce3ec] bg-white pr-8 text-[13px] text-[#374151]",
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


export function StudentPromotionManagementDashboard() {
  const [transitionKey, setTransitionKey] = useState("");
  const [programme, setProgramme] = useState("");

  const params = {
    transition_key: transitionKey || undefined,
    programme_code: programme || undefined,
  };

  const { data, isLoading, isError, error, refetch } = useStudentPromotionManagementPage(params);
  const previewMutation = usePreviewStudentPromotion();
  const promoteMutation = usePromoteEligibleStudents();

  useEffect(() => {
    if (data?.selected_transition_key && !transitionKey) {
      setTransitionKey(data.selected_transition_key);
    }
  }, [data?.selected_transition_key, transitionKey]);

  const filterParams = () => ({
    transition_key: transitionKey || data?.selected_transition_key,
    programme_code: programme || undefined,
  });

  const handlePreview = () => {
    previewMutation.mutate(filterParams(), {
      onSuccess: (res) => {
        if (res.preview_note) toast.message(res.preview_note);
        else toast.success("Preview updated.");
      },
      onError: (e: Error) => toast.error(e.message),
    });
  };

  const handlePromote = () => {
    const key = transitionKey || data?.selected_transition_key;
    if (!key) {
      toast.error("Select a promotion period first.");
      return;
    }
    promoteMutation.mutate(
      { transition_key: key, programme_code: programme || undefined },
      {
        onSuccess: () => toast.success("Eligible students promoted for the selected period."),
        onError: (e: Error) => toast.error(e.message),
      },
    );
  };

  return (
    <div className="space-y-5" data-figma-frame="158:5608">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Student Promotion Management"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">
            {data?.page_subtitle ?? "Promote students to the next semester"}
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <Button
            type="button"
            variant="outline"
            className="h-9 gap-1.5 border-[#dce3ec] text-xs font-medium text-[#374151]"
            onClick={handlePreview}
            disabled={isLoading || previewMutation.isPending}
          >
            <EyeIcon className="size-3.5" aria-hidden />
            {data?.preview_label ?? "Preview"}
          </Button>
          <Button
            type="button"
            className="h-9 gap-1.5 bg-[#245dd8] text-xs font-medium text-white hover:bg-[#1f4fb8]"
            onClick={handlePromote}
            disabled={isLoading || promoteMutation.isPending}
          >
            <CheckIcon className="size-3.5" aria-hidden />
            {data?.promote_eligible_label ?? "Promote eligible"}
          </Button>
        </div>
      </div>

      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-wrap items-center gap-2">
          <FilterSelect
            icon={<CalendarIcon className="size-3.5" aria-hidden />}
            label={data?.transition_filter_label ?? "Promotion period"}
            value={transitionKey}
            onChange={setTransitionKey}
            options={
              data?.transition_options?.length
                ? data.transition_options
                : [{ value: data?.selected_transition_key ?? "", label: "Promotion period" }]
            }
          />
          <FilterSelect
            icon={<FilterIcon className="size-3.5" aria-hidden />}
            label={data?.programme_filter_label ?? "Programme"}
            value={programme}
            onChange={setProgramme}
            options={data?.programme_options ?? [{ value: "", label: "All programmes" }]}
          />
        </div>
      </div>

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            {data.preview_note ? (
              <p className="rounded-lg border border-[#dbeafe] bg-[#eff6ff] px-4 py-2 text-[13px] text-[#1d4ed8]">
                {data.preview_note}
              </p>
            ) : null}

            <CollegeAdminKpiGrid>
              {data.kpis.map((kpi, index) => (
                <CollegeAdminUserDashboardKpiCard key={kpi.key} kpi={kpi} index={index} />
              ))}
            </CollegeAdminKpiGrid>

            <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.promotion_rules_section_title}</h3>
              </div>
              {data.promotion_rules_rows.length ? (
                <table className="w-full min-w-[32rem] text-left text-[13px]">
                  <thead>
                    <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                      {data.promotion_rules_table_headers.map((header, index) => (
                        <th
                          key={header}
                          className={cn(
                            "pb-3 font-medium",
                            index === 0 ? "px-5" : "pr-3",
                            index === data.promotion_rules_table_headers.length - 1 ? "pr-5" : "",
                          )}
                        >
                          {header}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#f1f5f9]">
                    {data.promotion_rules_rows.map((row) => (
                      <tr key={row.rule_key} className="text-[#374151]">
                        <td className="px-5 py-3 font-medium text-[#111827]">{row.rule_label}</td>
                        <td className="py-3 pr-3">{row.requirement_label}</td>
                        <td className="py-3 pr-5 tabular-nums text-[#6b7280]">{row.affected_label}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p className="px-5 py-8 text-sm text-[#9ca3af]">No promotion rules configured.</p>
              )}
              <div className="border-t border-[#f1f5f9] px-5 py-2.5 text-[12px] text-[#6b7280]">
                {data.promotion_rules_footer_label}
              </div>
            </section>

          </>
        ) : null}
      </QueryState>
    </div>
  );
}