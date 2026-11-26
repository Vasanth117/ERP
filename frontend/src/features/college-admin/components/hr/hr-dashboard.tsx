"use client";

import Link from "next/link";
import { useCallback, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  CollegeAdminChevronRight,
  CollegeAdminDownload,
  getCollegeAdminErpIcon,
  resolveCollegeAdminIconSlug,
} from "@/features/college-admin/components/layout/college-admin-erp-icons";
import {
  CollegeAdminKpiGrid,
  CollegeAdminUserDashboardKpiCard,
} from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useHrDashboardPage } from "@/features/college-admin/hooks/use-hr-dashboard";
import type { HrDashboardPage, HrDashboardPagination } from "@/features/college-admin/types/hr-dashboard";
import type { StudentAdminWorkQueueItem } from "@/features/college-admin/types/student-administration-dashboard";
import { cn } from "@/lib/utils";

const TABLE_HEADERS = ["Employee", "Leave type", "Dates", "Days", "Approver", "Status"];

const PLACEHOLDER_KPIS = [
  { key: "employees", label: "Employees", value: "—", hint_line: "0 faculty · 0 staff", hint_tone: "neutral" },
  { key: "vacancies", label: "Open vacancies", value: "—", hint_line: "Approved posts", hint_tone: "neutral" },
  { key: "on_leave_today", label: "On leave today", value: "—", hint_line: "Approved leave today", hint_tone: "neutral" },
  { key: "payroll", label: "Payroll", value: "—", hint_line: "Run due —", hint_tone: "neutral" },
];

const PLACEHOLDER_ATTENTION: StudentAdminWorkQueueItem[] = [
  {
    key: "leave_approvals",
    title: "Leave approvals",
    subtitle: "pending",
    count: 0,
    href: "/college-admin/hr/leave-approval",
    action_label: "Review →",
    icon_slug: "clock",
  },
  {
    key: "onboarding_tasks",
    title: "Onboarding tasks",
    subtitle: "overdue",
    count: 0,
    href: "/college-admin/hr/employee-onboarding",
    action_label: "Open →",
    icon_slug: "info",
  },
  {
    key: "contracts_ending",
    title: "Contracts ending in 60 days",
    subtitle: "employees",
    count: 0,
    href: "/college-admin/hr/employee-management",
    action_label: "View →",
    icon_slug: "calendar",
  },
  {
    key: "claims_review",
    title: "Claims awaiting review",
    subtitle: "benefit claims",
    count: 0,
    href: "/college-admin/hr/employee-benefits-claims",
    action_label: "Review →",
    icon_slug: "file-text",
  },
];

function StatusPill({ label, tone }: { label: string; tone: string }) {
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
  const key = tone in styles ? tone : "muted";
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-medium",
        styles[key],
      )}
    >
      <span className={cn("size-1.5 rounded-full", dot[key])} />
      {label}
    </span>
  );
}

function AttentionRow({ item }: { item: StudentAdminWorkQueueItem }) {
  const slug = resolveCollegeAdminIconSlug(item.icon_slug);
  const Icon = getCollegeAdminErpIcon(slug);
  const countTone =
    item.key === "leave_approvals" || item.key === "onboarding_tasks"
      ? "bg-[#fff7ed] text-[#c2410c]"
      : "bg-[#eff6ff] text-[#1d4ed8]";
  return (
    <li className="flex items-center justify-between gap-3 border-b border-[#f1f5f9] py-3.5 last:border-0">
      <div className="flex min-w-0 items-center gap-3">
        {Icon ? (
          <Icon className="size-[18px] shrink-0 text-[#9ca3af]" aria-hidden />
        ) : (
          <span className="size-[18px] shrink-0 rounded bg-[#f3f4f6]" aria-hidden />
        )}
        <div className="min-w-0">
          <p className="text-[13px] font-medium text-[#111827]">{item.title}</p>
          <p className="text-[12px] text-[#6b7280]">
            {item.count.toLocaleString("en-IN")} {item.subtitle}
          </p>
        </div>
      </div>
      <span
        className={cn(
          "inline-flex min-w-[1.75rem] shrink-0 items-center justify-center rounded-md px-1.5 py-0.5 text-[11px] font-semibold tabular-nums",
          countTone,
        )}
      >
        {item.count.toLocaleString("en-IN")}
      </span>
    </li>
  );
}

function TablePagination({
  pagination,
  onPage,
}: {
  pagination: HrDashboardPagination;
  onPage: (page: number) => void;
}) {
  if (pagination.total_pages <= 0) return null;
  return (
    <nav className="flex flex-wrap items-center justify-end gap-1" aria-label="Leave applications pagination">
      <button
        type="button"
        className="rounded border border-[#dce3ec] px-2 py-1 text-[12px] disabled:opacity-40"
        disabled={!pagination.has_previous}
        onClick={() => onPage(Math.max(1, pagination.page - 1))}
      >
        ‹
      </button>
      {pagination.page_numbers.map((num, idx) =>
        num === -1 ? (
          <span key={`ellipsis-${idx}`} className="px-1 text-[12px] text-[#9ca3af]">
            …
          </span>
        ) : (
          <button
            key={num}
            type="button"
            onClick={() => onPage(num)}
            className={cn(
              "min-w-[1.75rem] rounded px-1.5 py-0.5 text-[12px] tabular-nums",
              num === pagination.page
                ? "bg-[#245dd8] font-medium text-white"
                : "text-[#6b7280] hover:bg-[#f3f4f6]",
            )}
          >
            {num}
          </button>
        ),
      )}
      <button
        type="button"
        className="rounded border border-[#dce3ec] px-2 py-1 text-[12px] disabled:opacity-40"
        disabled={!pagination.has_next}
        onClick={() => onPage(pagination.page + 1)}
      >
        ›
      </button>
    </nav>
  );
}

function mergePage(data: HrDashboardPage | undefined): {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  open_portal_label: string;
  open_portal_href: string;
  kpis: typeof PLACEHOLDER_KPIS;
  leave_section_title: string;
  leave_view_all_href: string;
  leave_view_all_label: string;
  table_headers: string[];
  leave_rows: HrDashboardPage["leave_rows"];
  showing_label: string;
  pagination: HrDashboardPagination;
  needs_attention_title: string;
  needs_attention_items: StudentAdminWorkQueueItem[];
  generated_at?: string;
} {
  const emptyPagination: HrDashboardPagination = {
    page: 1,
    page_size: 4,
    total: 0,
    total_pages: 0,
    page_numbers: [],
    has_previous: false,
    has_next: false,
  };
  return {
    page_title: data?.page_title ?? "HR Dashboard",
    page_subtitle: data?.page_subtitle ?? "Workforce overview",
    export_label: data?.export_label ?? "Export",
    open_portal_label: data?.open_portal_label ?? "Open HR portal",
    open_portal_href: data?.open_portal_href ?? "/college-admin/hr/employee-management",
    kpis: data?.kpis?.length ? data.kpis : PLACEHOLDER_KPIS,
    leave_section_title: data?.leave_section_title ?? "Leave applications",
    leave_view_all_href: data?.leave_view_all_href ?? "/college-admin/hr/leave-management",
    leave_view_all_label: data?.leave_view_all_label ?? "View all →",
    table_headers: data?.table_headers?.length ? data.table_headers : TABLE_HEADERS,
    leave_rows: data?.leave_rows ?? [],
    showing_label: data?.showing_label ?? "Showing 0 of 0",
    pagination: data?.pagination ?? emptyPagination,
    needs_attention_title: data?.needs_attention_title ?? "Needs attention",
    needs_attention_items: data?.needs_attention_items?.length
      ? data.needs_attention_items
      : PLACEHOLDER_ATTENTION,
    generated_at: data?.generated_at,
  };
}

export function HrDashboard() {
  const [page, setPage] = useState(1);
  const queryParams = useMemo(() => ({ page, page_size: 4 }), [page]);
  const { data, isLoading, isError, error, refetch, isFetching } = useHrDashboardPage(queryParams);
  const view = mergePage(data);

  const handleExport = useCallback(() => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `hr-dashboard-${new Date(data.generated_at).toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data]);

  return (
    <div className="space-y-5" data-figma-frame="160:7148">
      <div className="flex flex-wrap items-center justify-end gap-2">
          <Button
            type="button"
            variant="outline"
            className="h-9 gap-1.5 border-[#dce3ec] text-xs font-medium text-[#374151]"
            onClick={handleExport}
            disabled={isLoading || !data}
          >
            <CollegeAdminDownload className="size-3.5" />
            {view.export_label}
          </Button>
          <Link
            href={view.open_portal_href}
            className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
          >
            {view.open_portal_label}
            <CollegeAdminChevronRight className="size-3.5" aria-hidden />
          </Link>
      </div>

      {isLoading || isFetching ? (
        <p className="text-[12px] text-[#9ca3af]">{isLoading ? "Loading workforce data…" : "Updating…"}</p>
      ) : null}

      {isError ? (
        <QueryState isError={isError} error={error} onRetry={() => void refetch()}>
          <></>
        </QueryState>
      ) : (
        <>
          <CollegeAdminKpiGrid>
            {view.kpis.map((kpi, index) => (
              <CollegeAdminUserDashboardKpiCard key={kpi.key} kpi={kpi} index={index} />
            ))}
          </CollegeAdminKpiGrid>

          <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_320px]">
            <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="flex items-center justify-between border-b border-[#f1f5f9] px-5 py-3.5">
                <h3 className="text-[14px] font-semibold text-[#111827]">{view.leave_section_title}</h3>
                <Link
                  href={view.leave_view_all_href}
                  className="text-[12px] font-medium text-[#245dd8] hover:underline"
                >
                  {view.leave_view_all_label}
                </Link>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[44rem] text-left text-[13px]">
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
                    {view.leave_rows.length ? (
                      view.leave_rows.map((row) => (
                        <tr key={row.leave_request_id} className="text-[#374151] hover:bg-[#f9fafb]">
                          <td className="pl-5 py-3 pr-3 font-medium text-[#111827]">
                            <Link href={row.detail_href} className="hover:text-[#245dd8]">
                              {row.employee_name}
                            </Link>
                          </td>
                          <td className="py-3 pr-3">{row.leave_type_label}</td>
                          <td className="py-3 pr-3 text-[#6b7280]">{row.dates_label}</td>
                          <td className="py-3 pr-3 tabular-nums">{row.days_label}</td>
                          <td className="py-3 pr-3 text-[#6b7280]">{row.approver_label}</td>
                          <td className="py-3 pr-5">
                            <StatusPill label={row.status_label} tone={row.status_tone} />
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={view.table_headers.length} className="px-5 py-10 text-center text-sm text-[#9ca3af]">
                          No leave applications yet.
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

            <section className="h-fit rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <h3 className="mb-1 text-[14px] font-semibold text-[#111827]">{view.needs_attention_title}</h3>
              <ul>
                {view.needs_attention_items.map((item) => (
                  <AttentionRow key={item.key} item={item} />
                ))}
              </ul>
            </section>
          </div>
        </>
      )}
    </div>
  );
}