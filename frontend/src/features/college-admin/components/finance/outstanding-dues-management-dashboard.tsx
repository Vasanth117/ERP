"use client";

import Link from "next/link";
import { useState } from "react";

import { InfoIcon } from "@/components/icons/erp/generated/info";
import {
  CollegeAdminKpiGrid,
  CollegeAdminUserDashboardKpiCard,
} from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { CollegeAdminPrimaryLink } from "@/features/college-admin/components/ui/college-admin-page-buttons";
import { FinancePaymentPagination } from "@/features/college-admin/components/finance/finance-payment-ui";
import { FinanceReceiptsSubNav } from "@/features/college-admin/components/finance/finance-receipts-sub-nav";
import { CollegeAdminPanelEmptyState } from "@/features/college-admin/components/ui/dashboard-panel-ui";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useOutstandingDuesManagementPage } from "@/features/college-admin/hooks/use-outstanding-dues-management";
import { cn } from "@/lib/utils";

const AGING_BAR: Record<string, string> = {
  green: "bg-[#10b981]",
  blue: "bg-[#245dd8]",
  amber: "bg-[#b45309]",
  error: "bg-[#dc2626]",
};

export function OutstandingDuesManagementDashboard() {
  const [page, setPage] = useState(1);
  const { data, isLoading, isError, error, refetch } = useOutstandingDuesManagementPage({ page });

  const remindersHref =
    data?.send_reminders_href ?? "/college-admin/finance/outstanding-dues-management?reminders=1";

  return (
    <div className="space-y-5" data-figma-frame="finance-outstanding-dues">
      {data?.sub_nav?.length ? <FinanceReceiptsSubNav items={data.sub_nav} /> : null}

      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Outstanding Dues Management"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">
            {data?.page_subtitle ?? "Overdue invoices and follow-up"}
          </p>
        </div>
        <CollegeAdminPrimaryLink href={remindersHref} className="shrink-0 gap-1.5">
          <InfoIcon className="size-3.5" aria-hidden />
          {data?.send_reminders_label ?? "Send reminders"}
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

            <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_300px]">
              <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                  <h3 className="text-[14px] font-semibold text-[#111827]">{data.dues_section_title}</h3>
                </div>
                {data.dues_rows.length ? (
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[36rem] text-left text-[13px]">
                      <thead>
                        <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                          {data.table_headers.map((header, index) => (
                            <th
                              key={header}
                              className={cn(
                                "pb-3 pt-4 font-medium",
                                index === 0 ? "pl-5 pr-3" : "pr-3",
                                index === data.table_headers.length - 1 ? "pr-5 text-right" : "",
                              )}
                            >
                              {header}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#f1f5f9]">
                        {data.dues_rows.map((row) => (
                          <tr key={`${row.student_name}-${row.invoice_label}`} className="hover:bg-[#f9fafb]">
                            <td className="pl-5 py-3 pr-3 font-medium text-[#111827]">
                              <Link href={row.detail_href} className="hover:text-[#245dd8]">
                                {row.student_name}
                              </Link>
                            </td>
                            <td className="py-3 pr-3 text-[12px] text-[#6b7280]">{row.invoice_label}</td>
                            <td className="py-3 pr-3 tabular-nums font-medium text-[#111827]">{row.balance_label}</td>
                            <td className="py-3 pr-5 text-right tabular-nums text-[#374151]">{row.overdue_label}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <CollegeAdminPanelEmptyState title="No outstanding dues" />
                )}
                <div className="flex flex-col gap-3 border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280] sm:flex-row sm:items-center sm:justify-between">
                  <span>{data.list_count_label || data.showing_label}</span>
                  {data.pagination.total_pages > 0 ? (
                    <FinancePaymentPagination pagination={data.pagination} page={page} setPage={setPage} />
                  ) : null}
                </div>
              </section>

              <aside className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.aging_section_title}</h3>
                <ul className="mt-4 space-y-4">
                  {data.aging_items.map((item) => (
                    <li key={item.bucket_key}>
                      <div className="mb-1.5 flex justify-between gap-2 text-[13px]">
                        <span className="font-medium text-[#111827]">{item.label}</span>
                        <span className="shrink-0 tabular-nums text-[#374151]">{item.amount_label}</span>
                      </div>
                      <div className="h-2 rounded-full bg-[#eef2f7]">
                        <div
                          className={cn(
                            "h-2 rounded-full",
                            AGING_BAR[item.bar_tone] ?? AGING_BAR.blue,
                          )}
                          style={{ width: `${Math.max(item.progress_percent, 4)}%` }}
                        />
                      </div>
                    </li>
                  ))}
                </ul>
              </aside>
            </div>
          </>
        ) : null}
      </QueryState>
    </div>
  );
}