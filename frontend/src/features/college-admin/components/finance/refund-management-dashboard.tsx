"use client";

import Link from "next/link";
import { useState } from "react";

import { CollegeAdminPlusActionLabel } from "@/features/college-admin/components/ui/college-admin-plus-action";
import {
  CollegeAdminKpiGrid,
  CollegeAdminUserDashboardKpiCard,
} from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { CollegeAdminPrimaryLink } from "@/features/college-admin/components/ui/college-admin-page-buttons";
import { FinanceAidSubNav } from "@/features/college-admin/components/finance/finance-aid-sub-nav";
import { FinancePaymentPagination, FinancePaymentStatusPill } from "@/features/college-admin/components/finance/finance-payment-ui";
import {
  CollegeAdminPanelEmptyState,
  CollegeAdminTablePanel,
} from "@/features/college-admin/components/ui/dashboard-panel-ui";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useRefundManagementPage } from "@/features/college-admin/hooks/use-refund-management-page";
import { cn } from "@/lib/utils";

export function RefundManagementDashboard() {
  const [page, setPage] = useState(1);
  const { data, isLoading, isError, error, refetch } = useRefundManagementPage({ page });

  return (
    <div className="space-y-5" data-figma-frame="finance-refunds">
      {data?.sub_nav?.length ? <FinanceAidSubNav items={data.sub_nav} /> : null}

      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Refund Management"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">
            {data?.page_subtitle ?? "Requested, approved, initiated and completed"}
          </p>
        </div>
        <CollegeAdminPrimaryLink
          href={data?.new_request_href ?? "/college-admin/finance/refund-management?create=1"}
          className="shrink-0"
        >
          <CollegeAdminPlusActionLabel iconClassName="size-3.5" label={data?.new_request_label ?? "New request"} />
        </CollegeAdminPrimaryLink>
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
              title={data.refunds_section_title}
              footer={
                <>
                  <span>{data.list_count_label}</span>
                  {data.pagination.total_pages > 0 ? (
                    <FinancePaymentPagination pagination={data.pagination} page={page} setPage={setPage} />
                  ) : null}
                </>
              }
            >
              {data.refund_rows.length ? (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[52rem] text-left text-[13px]">
                    <thead>
                      <tr className="border-b border-[#f1f5f9] text-[11px] font-semibold uppercase tracking-wide text-[#94a3b8]">
                        {data.table_headers.map((header, index) => (
                          <th
                            key={header}
                            className={cn(
                              "pb-3 pt-4 font-medium",
                              index === 0 ? "px-5" : "pr-3",
                              index === data.table_headers.length - 1 ? "pr-5 text-right" : "",
                              header === "Amount" ? "text-right" : "",
                            )}
                          >
                            {header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#f1f5f9]">
                      {data.refund_rows.map((row) => (
                        <tr key={row.refund_label} className="transition-colors hover:bg-[#f8fafc]">
                          <td className="px-5 py-3.5 font-mono text-[12px] font-medium text-[#111827]">
                            <Link href={row.detail_href} className="hover:text-[#245dd8]">
                              {row.refund_label}
                            </Link>
                          </td>
                          <td className="py-3.5 pr-3 text-[#374151]">{row.student_name}</td>
                          <td className="py-3.5 pr-3 font-mono text-[12px] text-[#6b7280]">
                            {row.original_transaction_label}
                          </td>
                          <td className="py-3.5 pr-3 text-right tabular-nums font-medium text-[#111827]">
                            {row.amount_label}
                          </td>
                          <td className="py-3.5 pr-3 text-[#374151]">{row.requested_label}</td>
                          <td className="py-3.5 pr-5 text-right">
                            <FinancePaymentStatusPill label={row.stage_label} tone={row.stage_tone} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <CollegeAdminPanelEmptyState title="No refund requests" />
              )}
            </CollegeAdminTablePanel>
          </>
        ) : null}
      </QueryState>
    </div>
  );
}