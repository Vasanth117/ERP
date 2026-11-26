"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { CollegeAdminPlusActionLabel } from "@/features/college-admin/components/ui/college-admin-plus-action";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { HrRecruitmentSubNav } from "@/features/college-admin/components/hr/hr-recruitment-sub-nav";
import { useHrEmployeeOnboardingPage } from "@/features/college-admin/hooks/use-hr-recruitment";
import type {
  HrEmployeeOnboardingPage,
  HrOnboardingStatusCell,
  HrRecruitmentPagination,
  HrRecruitmentSubNavItem,
} from "@/features/college-admin/types/hr-recruitment";
import { cn } from "@/lib/utils";

const TABLE_HEADERS = ["Employee", "Joining", "Documents", "IT account", "ID card", "Progress"];

const DEFAULT_SUB_NAV: HrRecruitmentSubNavItem[] = [
  { key: "recruitment", label: "Recruitment management", href: "/college-admin/hr/recruitment-management" },
  { key: "onboarding", label: "Employee onboarding", href: "/college-admin/hr/employee-onboarding" },
];

function StatusPill({ cell }: { cell: HrOnboardingStatusCell }) {
  const styles: Record<string, string> = {
    success: "bg-[#ecfdf5] text-[#047857]",
    warning: "bg-[#fff7ed] text-[#c2410c]",
    error: "bg-[#fef2f2] text-[#b91c1c]",
    info: "bg-[#eff6ff] text-[#1d4ed8]",
    muted: "bg-[#f3f4f6] text-[#6b7280]",
  };
  const dot: Record<string, string> = {
    success: "bg-[#10b981]",
    warning: "bg-[#f97316]",
    error: "bg-[#ef4444]",
    info: "bg-[#3b82f6]",
    muted: "bg-[#9ca3af]",
  };
  const key = cell.tone in styles ? cell.tone : "muted";
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-medium",
        styles[key],
      )}
    >
      <span className={cn("size-1.5 rounded-full", dot[key])} />
      {cell.label}
    </span>
  );
}

function TablePagination({
  pagination,
  onPage,
}: {
  pagination: HrRecruitmentPagination;
  onPage: (page: number) => void;
}) {
  if (pagination.total_pages <= 0) return null;
  return (
    <div className="flex items-center gap-1">
      <button
        type="button"
        className="rounded border border-[#dce3ec] px-2 py-1 disabled:opacity-40"
        disabled={!pagination.has_previous}
        onClick={() => onPage(Math.max(1, pagination.page - 1))}
      >
        ‹
      </button>
      {pagination.page_numbers.map((num, index) =>
        num === -1 ? (
          <span key={`ellipsis-${index}`} className="px-1">
            …
          </span>
        ) : (
          <button
            key={num}
            type="button"
            className={cn(
              "min-w-8 rounded border px-2 py-1 tabular-nums",
              num === pagination.page
                ? "border-[#245dd8] bg-[#eff6ff] text-[#245dd8]"
                : "border-[#dce3ec]",
            )}
            onClick={() => onPage(num)}
          >
            {num}
          </button>
        ),
      )}
      <button
        type="button"
        className="rounded border border-[#dce3ec] px-2 py-1 disabled:opacity-40"
        disabled={!pagination.has_next}
        onClick={() => onPage(pagination.page + 1)}
      >
        ›
      </button>
    </div>
  );
}

function mergeView(data: HrEmployeeOnboardingPage | undefined) {
  const emptyPagination: HrRecruitmentPagination = {
    page: 1,
    page_size: 4,
    total: 0,
    total_pages: 0,
    page_numbers: [],
    has_previous: false,
    has_next: false,
  };
  return {
    page_title: data?.page_title ?? "Employee Onboarding",
    page_subtitle: data?.page_subtitle ?? "Joining checklists for new employees",
    new_onboarding_label: data?.new_onboarding_label ?? "New onboarding",
    new_onboarding_href: data?.new_onboarding_href ?? "/college-admin/hr/employee-onboarding?create=1",
    sub_nav: data?.sub_nav?.length ? data.sub_nav : DEFAULT_SUB_NAV,
    onboarding_section_title: data?.onboarding_section_title ?? "Onboarding",
    table_headers: data?.table_headers?.length ? data.table_headers : TABLE_HEADERS,
    onboarding_rows: data?.onboarding_rows ?? [],
    showing_label: data?.showing_label ?? "0 of 0",
    pagination: data?.pagination ?? emptyPagination,
    footer_disclaimer: data?.footer_disclaimer ?? "Live institutional data · HR onboarding records · All times IST",
    footer_snapshot_label: data?.footer_snapshot_label ?? "",
  };
}

export function EmployeeOnboardingDashboard() {
  const [page, setPage] = useState(1);
  const queryParams = useMemo(() => ({ page, page_size: 4 }), [page]);
  const { data, isLoading, isError, error, refetch, isFetching } = useHrEmployeeOnboardingPage(queryParams);
  const view = mergeView(data);

  return (
    <div className="space-y-5" data-figma-frame="160:8204">
      <HrRecruitmentSubNav items={view.sub_nav} />

      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">{view.page_title}</h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">{view.page_subtitle}</p>
        </div>
        <Link
          href={view.new_onboarding_href}
          className="inline-flex h-9 shrink-0 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
        >
          <CollegeAdminPlusActionLabel iconClassName="size-3.5" label={view.new_onboarding_label} />
        </Link>
      </div>

      {isLoading || isFetching ? (
        <p className="text-[12px] text-[#9ca3af]">{isLoading ? "Loading onboarding data…" : "Updating…"}</p>
      ) : null}

      {isError ? <QueryState isError={isError} error={error} onRetry={() => void refetch()} /> : null}

      {!isError ? (
        <>
          <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
            <div className="border-b border-[#f1f5f9] px-5 py-3.5">
              <h3 className="text-[14px] font-semibold text-[#111827]">{view.onboarding_section_title}</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[52rem] text-left text-[13px]">
                <thead>
                  <tr className="border-b border-[#f1f5f9] text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                    {view.table_headers.map((header, index) => (
                      <th
                        key={header}
                        className={cn(
                          "pb-3 pt-4 font-medium",
                          index === 0 ? "pl-5 pr-3" : "pr-3",
                          index === view.table_headers.length - 1 ? "pr-5" : "",
                        )}
                      >
                        {header}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#f1f5f9]">
                  {view.onboarding_rows.length ? (
                    view.onboarding_rows.map((row) => (
                      <tr key={row.process_id} className="hover:bg-[#f9fafb]">
                        <td className="pl-5 py-3 pr-3 font-medium text-[#111827]">
                          <Link href={row.detail_href} className="hover:text-[#245dd8]">
                            {row.employee_name}
                          </Link>
                        </td>
                        <td className="py-3 pr-3 text-[#6b7280]">{row.joining_label}</td>
                        <td className="py-3 pr-3">
                          <StatusPill cell={row.documents} />
                        </td>
                        <td className="py-3 pr-3">
                          <StatusPill cell={row.it_account} />
                        </td>
                        <td className="py-3 pr-3">
                          <StatusPill cell={row.id_card} />
                        </td>
                        <td className="py-3 pr-5">
                          <StatusPill cell={row.progress} />
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={view.table_headers.length} className="px-5 py-10 text-center text-sm text-[#9ca3af]">
                        No onboarding records yet. Start onboarding when a new hire is confirmed.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
            <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
              <span>{view.showing_label}</span>
              <TablePagination pagination={view.pagination} onPage={setPage} />
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