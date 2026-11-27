"use client";
import { CollegeAdminModulePageHeading } from "@/features/college-admin/components/layout/college-admin-module-page-heading";
import { CollegeAdminPlusActionLabel } from "@/features/college-admin/components/ui/college-admin-plus-action";

import Link from "next/link";
import { useCallback, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  CollegeAdminDownload,
  getCollegeAdminErpIcon,
  resolveCollegeAdminIconSlug,
} from "@/features/college-admin/components/layout/college-admin-erp-icons";
import {
  CollegeAdminKpiGrid,
  CollegeAdminUserDashboardKpiCard,
} from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useExaminationDashboardPage } from "@/features/college-admin/hooks/use-examination-dashboard";
import type { StudentAdminWorkQueueItem } from "@/features/college-admin/types/student-administration-dashboard";
import { cn } from "@/lib/utils";

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

function PendingRow({ item }: { item: StudentAdminWorkQueueItem }) {
  const slug = resolveCollegeAdminIconSlug(item.icon_slug);
  const Icon = getCollegeAdminErpIcon(slug);
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
          <p className="text-[12px] text-[#6b7280]">{item.subtitle}</p>
        </div>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <span className="inline-flex min-w-[1.75rem] justify-center rounded-full bg-[#fff7ed] px-2 py-0.5 text-[11px] font-semibold tabular-nums text-[#c2410c]">
          {item.count.toLocaleString("en-IN")}
        </span>
        <Link href={item.href} className="text-[12px] font-medium text-[#245dd8] hover:underline">
          {item.action_label}
        </Link>
      </div>
    </li>
  );
}


export function ExaminationDashboard() {
  const [page, setPage] = useState(1);
  const { data, isLoading, isError, error, refetch } = useExaminationDashboardPage({ page });

  const handleExport = useCallback(() => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `examination-dashboard-${new Date(data.generated_at).toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data]);

  return (
    <div className="space-y-5" data-figma-frame="159:10708">
      <CollegeAdminModulePageHeading title={data?.page_title ?? "Examination Dashboard"} subtitle={data?.page_subtitle ?? "Exam sessions, registration and results"} actions={<><Button
            type="button"
            variant="outline"
            className="h-9 gap-1.5 border-[#dce3ec] text-xs font-medium text-[#374151]"
            onClick={handleExport}
            disabled={isLoading || !data}
          >
            <CollegeAdminDownload className="size-3.5" />
            {data?.export_label ?? "Export"}
          </Button>
          <Link
            href={data?.create_examination_href ?? "/college-admin/examinations/examination-configuration?mode=new"}
            className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
          >
            <CollegeAdminPlusActionLabel iconClassName="size-3.5" label={data?.create_examination_label ?? "Create examination" } />
          </Link></>} />


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
                <div className="flex items-center justify-between border-b border-[#f1f5f9] px-5 py-3.5">
                  <h3 className="text-[14px] font-semibold text-[#111827]">{data.sessions_section_title}</h3>
                  <span className="text-[12px] text-[#6b7280]">{data.sessions_count_label}</span>
                </div>
                {data.session_rows.length ? (
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[44rem] text-left text-[13px]">
                      <thead>
                        <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                          {data.table_headers.map((header, index) => (
                            <th
                              key={header}
                              className={cn(
                                "pb-3 font-medium",
                                index === 0 ? "pl-5 pr-3" : "pr-3",
                                index === data.table_headers.length - 1 ? "pr-5" : "",
                              )}
                            >
                              {header}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#f1f5f9]">
                        {data.session_rows.map((row) => (
                          <tr key={row.session_id} className="text-[#374151] hover:bg-[#f9fafb]">
                            <td className="pl-5 py-3 pr-3 font-medium text-[#111827]">
                              <Link href={row.detail_href} className="hover:text-[#245dd8]">
                                {row.session_label}
                              </Link>
                            </td>
                            <td className="py-3 pr-3">{row.type_label}</td>
                            <td className="py-3 pr-3 text-[12px] text-[#6b7280]">{row.period_label}</td>
                            <td className="py-3 pr-3">{row.programmes_label}</td>
                            <td className="py-3 pr-3 tabular-nums">{row.students_count.toLocaleString("en-IN")}</td>
                            <td className="py-3 pr-5">
                              <StatusPill label={row.status_label} tone={row.status_tone} />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="px-5 py-10 text-center text-sm text-[#9ca3af]">No examination sessions yet.</p>
                )}
                <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
                  <span>{data.showing_label}</span>
                  {data.pagination.total_pages > 0 ? (
                    <div className="flex items-center gap-1">
                      <button
                        type="button"
                        className="rounded border border-[#dce3ec] px-2 py-1 disabled:opacity-40"
                        disabled={!data.pagination.has_previous}
                        onClick={() => setPage((p) => Math.max(1, p - 1))}
                      >
                        ‹
                      </button>
                      {data.pagination.page_numbers.map((num, index) =>
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
                              num === data.pagination.page
                                ? "border-[#245dd8] bg-[#eff6ff] text-[#245dd8]"
                                : "border-[#dce3ec]",
                            )}
                            onClick={() => setPage(num)}
                          >
                            {num}
                          </button>
                        ),
                      )}
                      <button
                        type="button"
                        className="rounded border border-[#dce3ec] px-2 py-1 disabled:opacity-40"
                        disabled={!data.pagination.has_next}
                        onClick={() => setPage((p) => p + 1)}
                      >
                        ›
                      </button>
                    </div>
                  ) : null}
                </div>
              </section>

              <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <h3 className="mb-1 text-[14px] font-semibold text-[#111827]">{data.pending_title}</h3>
                <ul>{data.pending_items.map((item) => <PendingRow key={item.key} item={item} />)}</ul>
              </section>
            </div>

          </>
        ) : null}
      </QueryState>
    </div>
  );
}