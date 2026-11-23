"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { LockIcon } from "@/components/icons/erp/generated/lock";
import { PlusIcon } from "@/components/icons/erp/generated/plus";
import { YearsSemestersSubNav } from "@/features/college-admin/components/academics/years-semesters-sub-nav";
import {
  CollegeAdminPanelEmptyState,
  CollegeAdminPanelShell,
  CollegeAdminPanelChromeHeader,
  CollegeAdminPanelChromeFooter,
  CollegeAdminSidePanel,
  CollegeAdminTablePanel,
} from "@/features/college-admin/components/ui/dashboard-panel-ui";
import {
  CollegeAdminPrimaryLink,
  CollegeAdminSecondaryButton,
} from "@/features/college-admin/components/ui/college-admin-action-button";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useAcademicYearManagementPage,
  useCloseCurrentAcademicYear,
  useSaveAcademicYearManagementRules,
} from "@/features/college-admin/hooks/use-academic-year-management";
import type { AcademicYearRuleToggle } from "@/features/college-admin/types/academic-year-management";
import { cn } from "@/lib/utils";

function StatusPill({ label, tone }: { label: string; tone: string }) {
  const styles: Record<string, string> = {
    success: "bg-[#ecfdf5] text-[#047857]",
    warning: "bg-[#fff7ed] text-[#c2410c]",
    info: "bg-[#eff6ff] text-[#1d4ed8]",
    muted: "bg-[#f3f4f6] text-[#6b7280]",
  };
  const dot: Record<string, string> = {
    success: "bg-[#10b981]",
    warning: "bg-[#f97316]",
    info: "bg-[#3b82f6]",
    muted: "bg-[#9ca3af]",
  };
  const key = tone in styles ? tone : "muted";
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-medium", styles[key])}>
      <span className={cn("size-1.5 rounded-full", dot[key])} />
      {label}
    </span>
  );
}

function RuleToggle({
  rule,
  checked,
  onChange,
}: {
  rule: AcademicYearRuleToggle;
  checked: boolean;
  onChange: (next: boolean) => void;
}) {
  return (
    <div className="flex items-start justify-between gap-3 py-3.5 first:pt-1">
      <div>
        <p className="text-[13px] font-medium text-[#111827]">{rule.title}</p>
        <p className="text-[12px] text-[#6b7280]">{rule.description}</p>
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        aria-label={rule.title}
        onClick={() => onChange(!checked)}
        className={cn(
          "relative h-6 w-11 shrink-0 rounded-full transition-colors",
          checked ? "bg-[#245dd8]" : "bg-[#d1d5db]",
        )}
      >
        <span
          className={cn(
            "absolute top-0.5 size-5 rounded-full bg-white shadow transition-transform",
            checked ? "left-[22px]" : "left-0.5",
          )}
        />
      </button>
    </div>
  );
}

export function AcademicYearManagementDashboard() {
  const [page, setPage] = useState(1);
  const { data, isLoading, isError, error, refetch } = useAcademicYearManagementPage(page);
  const closeYear = useCloseCurrentAcademicYear();
  const saveRules = useSaveAcademicYearManagementRules();

  const [rulesState, setRulesState] = useState<Record<string, boolean>>({});

  useEffect(() => {
    if (!data?.rules) return;
    const next: Record<string, boolean> = {};
    for (const rule of data.rules) {
      next[rule.key] = rule.enabled;
    }
    setRulesState(next);
  }, [data?.rules]);

  const persistRules = (key: string, enabled: boolean) => {
    const next = {
      ...rulesState,
      [key]: enabled,
    };
    setRulesState(next);
    saveRules.mutate({
      only_one_current_year: next.only_one_current_year ?? true,
      lock_closed_years: next.lock_closed_years ?? true,
    });
  };

  const createHref =
    data?.new_academic_year_href ?? "/college-admin/academics/create-academic-year";

  return (
    <div className="space-y-5" data-figma-frame="69:139876">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Academic Year Management"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">
            {data?.page_subtitle ?? "Create, open and close academic years"}
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap items-center gap-2">
          <CollegeAdminSecondaryButton
            disabled={!data?.close_current_year_enabled || closeYear.isPending}
            onClick={() => closeYear.mutate()}
          >
            <LockIcon className="size-3.5 shrink-0" aria-hidden />
            {data?.close_current_year_label ?? "Close current year"}
          </CollegeAdminSecondaryButton>
          <CollegeAdminPrimaryLink href={createHref}>
            <PlusIcon className="size-3.5 shrink-0" aria-hidden />
            {data?.new_academic_year_label ?? "New academic year"}
          </CollegeAdminPrimaryLink>
        </div>
      </div>

      {data?.sub_nav?.length ? <YearsSemestersSubNav items={data.sub_nav} /> : null}

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_360px]">
              <CollegeAdminTablePanel
                title={data.academic_years_table_title}
                footer={
                  <>
                    <span>{data.academic_year_count_label}</span>
                    {data.total_pages > 1 ? (
                      <div className="flex items-center gap-1">
                        {Array.from({ length: data.total_pages }, (_, i) => i + 1).map((p) => (
                          <button
                            key={p}
                            type="button"
                            onClick={() => setPage(p)}
                            className={cn(
                              "inline-flex size-8 items-center justify-center rounded-md border text-xs font-semibold transition-colors",
                              p === data.page
                                ? "border-[#245dd8] bg-[#eff6ff] text-[#245dd8]"
                                : "border-[#e5e7eb] bg-white text-[#64748b] hover:border-[#dce3ec] hover:bg-white",
                            )}
                          >
                            {p}
                          </button>
                        ))}
                      </div>
                    ) : null}
                  </>
                }
              >
                {data.academic_years.length ? (
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[36rem] text-left text-[13px]">
                      <thead>
                        <tr className="border-b border-[#f1f5f9] text-[11px] font-semibold uppercase tracking-wide text-[#94a3b8]">
                          {data.table_headers.map((header, index) => (
                            <th key={header} className={cn("pb-3 pt-4 font-medium", index === 0 ? "px-5" : "pr-3")}>
                              {header}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#f1f5f9]">
                        {data.academic_years.map((row) => (
                          <tr key={row.year_id} className="transition-colors hover:bg-[#f8fafc]">
                            <td className="px-5 py-3.5 font-medium text-[#111827]">
                              <Link
                                href={row.detail_href ?? `/college-admin/academics/academic-year-details?year_id=${row.year_id}`}
                                className="hover:text-[#245dd8]"
                              >
                                {row.label}
                              </Link>
                            </td>
                            <td className="py-3.5 pr-3 text-[#374151]">{row.start_label}</td>
                            <td className="py-3.5 pr-3 text-[#374151]">{row.end_label}</td>
                            <td className="py-3.5 pr-3 tabular-nums text-[#374151]">
                              {row.student_count.toLocaleString("en-IN")}
                            </td>
                            <td className="py-3.5 pr-5">
                              <StatusPill label={row.status_label} tone={row.status_tone} />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <CollegeAdminPanelEmptyState
                    iconSlug="calendar-days"
                    title="No academic years yet"
                    description="Start by creating an academic year with start and end dates, then add semesters and calendar events."
                    action={
                      <CollegeAdminPrimaryLink href={createHref}>
                        <PlusIcon className="size-3.5 shrink-0" aria-hidden />
                        {data.new_academic_year_label}
                      </CollegeAdminPrimaryLink>
                    }
                  />
                )}
              </CollegeAdminTablePanel>

              <div className="space-y-5">
                <CollegeAdminSidePanel title={data.checklist_title}>
                  <ul className="space-y-3 border-l-2 border-[#e8ecf2] pl-4">
                    {data.checklist_items.map((item) => (
                      <li key={item.key} className="relative pl-2">
                        <span
                          className={cn(
                            "absolute -left-[22px] top-1.5 size-2.5 rounded-full ring-4 ring-white",
                            item.completed ? "bg-[#10b981]" : "bg-[#3b82f6]",
                          )}
                        />
                        <p className="text-[13px] font-medium text-[#111827]">{item.title}</p>
                        {item.detail ? <p className="text-[12px] text-[#64748b]">{item.detail}</p> : null}
                      </li>
                    ))}
                  </ul>
                </CollegeAdminSidePanel>

                <CollegeAdminPanelShell>
                  <CollegeAdminPanelChromeHeader title={data.rules_section_title} />
                  <div className="divide-y divide-[#f1f5f9] px-5">
                    {data.rules.map((rule) => (
                      <RuleToggle
                        key={rule.key}
                        rule={rule}
                        checked={rulesState[rule.key] ?? rule.enabled}
                        onChange={(next) => persistRules(rule.key, next)}
                      />
                    ))}
                  </div>
                </CollegeAdminPanelShell>
              </div>
            </div>
          </>
        ) : null}
      </QueryState>
    </div>
  );
}