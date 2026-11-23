"use client";
import { CollegeAdminPlusActionLabel } from "@/features/college-admin/components/ui/college-admin-plus-action";

import Link from "next/link";
import { useState } from "react";

import { SendIcon } from "@/components/icons/erp/generated/send";
import { Button } from "@/components/ui/button";
import { CollegeAdminOutlineLink } from "@/features/college-admin/components/ui/college-admin-page-buttons";
import {
  CollegeAdminKpiGrid,
  CollegeAdminUserDashboardKpiCard,
} from "@/features/college-admin/components/ui/college-admin-kpi-card";
import {
  CollegeAdminPanelEmptyState,
  CollegeAdminTablePanel,
} from "@/features/college-admin/components/ui/dashboard-panel-ui";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useFeeDemandInvoiceManagementPage } from "@/features/college-admin/hooks/use-fee-demand-invoice-management";
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

function Pagination({
  data,
  page,
  setPage,
}: {
  data: NonNullable<ReturnType<typeof useFeeDemandInvoiceManagementPage>["data"]>;
  page: number;
  setPage: (n: number) => void;
}) {
  return (
    <div className="flex items-center gap-1">
      <button
        type="button"
        className="rounded border border-[#dce3ec] px-2 py-1 disabled:opacity-40"
        disabled={!data.pagination.has_previous}
        onClick={() => setPage(Math.max(1, page - 1))}
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
              "min-w-8 rounded border px-2 py-1 tabular-nums text-xs font-semibold",
              num === data.pagination.page ? "border-[#245dd8] bg-[#eff6ff] text-[#245dd8]" : "border-[#dce3ec]",
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
        onClick={() => setPage(page + 1)}
      >
        ›
      </button>
    </div>
  );
}

export function FeeDemandInvoiceManagementDashboard() {
  const [page, setPage] = useState(1);
  const { data, isLoading, isError, error, refetch } = useFeeDemandInvoiceManagementPage({ page });

  const generateHref = data?.generate_demands_href ?? "/college-admin/finance/fee-demand-invoice-management?generate=1";
  const publishHref = data?.publish_href ?? "/college-admin/finance/fee-demand-invoice-management?publish=1";
  const headers = data?.table_headers ?? [];

  return (
    <div className="space-y-5" data-figma-frame="160:3264">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Fee Demand & Invoice Management"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">
            {data?.page_subtitle ?? "Generate and publish fee demands"}
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <CollegeAdminOutlineLink href={generateHref}>
            <CollegeAdminPlusActionLabel
              iconClassName="size-3.5"
              label={data?.generate_demands_label ?? "Generate demands"}
            />
          </CollegeAdminOutlineLink>
          <Button
            type="button"
            className="h-9 gap-1.5 bg-[#245dd8] px-4 text-xs font-medium hover:bg-[#1f4fb8]"
            asChild
          >
            <Link href={publishHref}>
              <SendIcon className="size-3.5" aria-hidden />
              {data?.publish_label ?? "Publish"}
            </Link>
          </Button>
        </div>
      </div>

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            <CollegeAdminKpiGrid>
              {data.kpis.map((kpi, index) => (
                <CollegeAdminUserDashboardKpiCard key={kpi.key} kpi={kpi} index={index} />
              ))}
            </CollegeAdminKpiGrid>

            <CollegeAdminTablePanel
              title={data.invoices_section_title}
              description={data.invoices_count_label}
              footer={
                <>
                  <span>{data.showing_label}</span>
                  {data.pagination.total_pages > 0 ? (
                    <Pagination data={data} page={page} setPage={setPage} />
                  ) : null}
                </>
              }
            >
              {data.invoice_rows.length ? (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[44rem] text-left text-[13px]">
                    <thead>
                      <tr className="border-b border-[#f1f5f9] text-[11px] font-semibold uppercase tracking-wide text-[#94a3b8]">
                        {headers.map((header, index) => (
                          <th
                            key={header}
                            className={cn(
                              "pb-3 pt-4 font-medium",
                              index === 0 ? "px-5" : "pr-3",
                              index === headers.length - 1 ? "pr-5 text-right" : "",
                              header === "Total" || header === "Paid" ? "text-right" : "",
                            )}
                          >
                            {header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#f1f5f9]">
                      {data.invoice_rows.map((row) => (
                        <tr key={row.invoice_id} className="transition-colors hover:bg-[#f8fafc]">
                          <td className="px-5 py-3.5 font-medium text-[#111827]">
                            <Link href={row.detail_href} className="hover:text-[#245dd8]">
                              {row.invoice_label}
                            </Link>
                          </td>
                          <td className="py-3.5 pr-3 text-[#374151]">{row.student_name}</td>
                          <td className="py-3.5 pr-3 text-[12px] text-[#6b7280]">{row.due_label}</td>
                          <td className="py-3.5 pr-3 text-right tabular-nums font-medium text-[#111827]">
                            {row.total_label}
                          </td>
                          <td className="py-3.5 pr-3 text-right tabular-nums text-[#374151]">{row.paid_label}</td>
                          <td className="py-3.5 pr-5 text-right">
                            <StatusPill label={row.status_label} tone={row.status_tone} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <CollegeAdminPanelEmptyState
                  iconSlug="file-text"
                  title="No invoices yet"
                  description="Generate fee demands from assessed students, then publish invoices for payment collection."
                  action={
                    <CollegeAdminOutlineLink href={generateHref}>
                      <CollegeAdminPlusActionLabel iconClassName="size-3.5" label={data.generate_demands_label} />
                    </CollegeAdminOutlineLink>
                  }
                />
              )}
            </CollegeAdminTablePanel>
          </>
        ) : null}
      </QueryState>
    </div>
  );
}