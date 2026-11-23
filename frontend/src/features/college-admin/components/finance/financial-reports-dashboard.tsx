"use client";

import Link from "next/link";
import { useState } from "react";

import { CollegeAdminPlusActionLabel } from "@/features/college-admin/components/ui/college-admin-plus-action";
import { CollegeAdminPrimaryLink } from "@/features/college-admin/components/ui/college-admin-page-buttons";
import { FinanceReconciliationSubNav } from "@/features/college-admin/components/finance/finance-reconciliation-sub-nav";
import { FinancePaymentPagination } from "@/features/college-admin/components/finance/finance-payment-ui";
import {
  CollegeAdminPanelEmptyState,
  CollegeAdminTablePanel,
} from "@/features/college-admin/components/ui/dashboard-panel-ui";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useFinancialReportsPage } from "@/features/college-admin/hooks/use-financial-reports-page";
import { cn } from "@/lib/utils";

export function FinancialReportsDashboard() {
  const [page, setPage] = useState(1);
  const { data, isLoading, isError, error, refetch } = useFinancialReportsPage({ page });

  return (
    <div className="space-y-5" data-figma-frame="finance-reports">
      {data?.sub_nav?.length ? <FinanceReconciliationSubNav items={data.sub_nav} /> : null}

      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Financial Reports"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">
            {data?.page_subtitle ?? "Collection, dues and refund reports"}
          </p>
        </div>
        <CollegeAdminPrimaryLink
          href={data?.create_report_href ?? "/college-admin/finance/financial-reports?create=1"}
          className="shrink-0"
        >
          <CollegeAdminPlusActionLabel iconClassName="size-3.5" label={data?.create_report_label ?? "Create report"} />
        </CollegeAdminPrimaryLink>
      </div>

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <CollegeAdminTablePanel
            title={data.reports_section_title}
            footer={
              <>
                <span>{data.list_count_label}</span>
                {data.pagination.total_pages > 1 ? (
                  <FinancePaymentPagination pagination={data.pagination} page={page} setPage={setPage} />
                ) : null}
              </>
            }
          >
            {data.report_rows.length ? (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[48rem] text-left text-[13px]">
                  <thead>
                    <tr className="border-b border-[#f1f5f9] text-[11px] font-semibold uppercase tracking-wide text-[#94a3b8]">
                      {data.table_headers.map((header, index) => (
                        <th
                          key={header}
                          className={cn(
                            "pb-3 pt-4 font-medium",
                            index === 0 ? "px-5" : "pr-3",
                            index === data.table_headers.length - 1 ? "pr-5 text-right" : "",
                            index > 0 ? "text-right" : "",
                          )}
                        >
                          {header}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#f1f5f9]">
                    {data.report_rows.map((row) => (
                      <tr key={row.report_key} className="transition-colors hover:bg-[#f8fafc]">
                        <td className="px-5 py-3.5 font-semibold text-[#111827]">
                          <Link href={row.detail_href} className="hover:text-[#245dd8]">
                            {row.report_label}
                          </Link>
                        </td>
                        <td className="py-3.5 pr-3 text-right text-[#374151]">{row.period_label}</td>
                        <td className="py-3.5 pr-3 text-right text-[#374151]">{row.format_label}</td>
                        <td className="py-3.5 pr-3 text-right text-[#374151]">{row.last_run_label}</td>
                        <td className="py-3.5 pr-5 text-right text-[#374151]">{row.schedule_label}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <CollegeAdminPanelEmptyState title="No reports configured" />
            )}
          </CollegeAdminTablePanel>
        ) : null}
      </QueryState>
    </div>
  );
}