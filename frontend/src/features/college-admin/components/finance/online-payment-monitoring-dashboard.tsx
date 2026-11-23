"use client";

import Link from "next/link";
import { useState } from "react";

import { CircleCheckIcon } from "@/components/icons/erp/generated/circle-check";
import { InfoIcon } from "@/components/icons/erp/generated/info";
import {
  CollegeAdminKpiGrid,
  CollegeAdminUserDashboardKpiCard,
} from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { CollegeAdminPrimaryLink } from "@/features/college-admin/components/ui/college-admin-page-buttons";
import { CollegeAdminRefreshCw } from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { FinancePaymentPagination, FinancePaymentStatusPill } from "@/features/college-admin/components/finance/finance-payment-ui";
import { FinancePaymentsSubNav } from "@/features/college-admin/components/finance/finance-payments-sub-nav";
import { CollegeAdminPanelEmptyState } from "@/features/college-admin/components/ui/dashboard-panel-ui";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useOnlinePaymentMonitoringPage } from "@/features/college-admin/hooks/use-online-payment-monitoring";
import { cn } from "@/lib/utils";

function GatewayBadge({ label, tone }: { label: string; tone: string }) {
  const styles: Record<string, string> = {
    success: "bg-[#ecfdf5] text-[#047857]",
    warning: "bg-[#fff7ed] text-[#c2410c]",
  };
  const key = tone in styles ? tone : "success";
  return (
    <span className={cn("rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide", styles[key])}>
      {label}
    </span>
  );
}

export function OnlinePaymentMonitoringDashboard() {
  const [page, setPage] = useState(1);
  const { data, isLoading, isError, error, refetch } = useOnlinePaymentMonitoringPage({ page });

  return (
    <div className="space-y-5" data-figma-frame="finance-payments-online">
      {data?.sub_nav?.length ? <FinancePaymentsSubNav items={data.sub_nav} /> : null}

      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Online Payment Monitoring"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">
            {data?.page_subtitle ?? "Gateway transactions and settlements"}
          </p>
        </div>
        <CollegeAdminPrimaryLink
          href={data?.verify_pending_href ?? "/college-admin/finance/online-payment-monitoring?verify=1"}
          className="shrink-0 gap-1.5"
        >
          <CollegeAdminRefreshCw className="size-3.5" aria-hidden />
          {data?.verify_pending_label ?? "Verify pending"}
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
                  <h3 className="text-[14px] font-semibold text-[#111827]">{data.transactions_section_title}</h3>
                </div>
                {data.transaction_rows.length ? (
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[40rem] text-left text-[13px]">
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
                        {data.transaction_rows.map((row) => (
                          <tr key={row.transaction_id} className="text-[#374151] hover:bg-[#f9fafb]">
                            <td className="pl-5 py-3 pr-3 font-medium text-[#111827]">
                              <Link href={row.detail_href} className="hover:text-[#245dd8]">
                                {row.transaction_id}
                              </Link>
                            </td>
                            <td className="py-3 pr-3">{row.student_name}</td>
                            <td className="py-3 pr-3 text-[12px] text-[#6b7280]">{row.invoice_label}</td>
                            <td className="py-3 pr-3">{row.method_label}</td>
                            <td className="py-3 pr-3 tabular-nums font-medium text-[#111827]">{row.amount_label}</td>
                            <td className="py-3 pr-5 text-right">
                              <FinancePaymentStatusPill label={row.status_label} tone={row.status_tone} />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <CollegeAdminPanelEmptyState title="No online transactions yet" />
                )}
                <div className="flex flex-col gap-3 border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280] sm:flex-row sm:items-center sm:justify-between">
                  <span>{data.showing_label}</span>
                  {data.pagination.total_pages > 0 ? (
                    <FinancePaymentPagination pagination={data.pagination} page={page} setPage={setPage} />
                  ) : null}
                </div>
              </section>

              <aside className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.gateways_section_title}</h3>
                <ul className="mt-4 space-y-4">
                  {data.gateway_items.map((item) => (
                    <li key={item.gateway_key} className="flex items-start justify-between gap-2">
                      <div className="flex gap-2">
                        {item.icon_variant === "check" ? (
                          <CircleCheckIcon className="mt-0.5 size-4 text-[#10b981]" aria-hidden />
                        ) : (
                          <InfoIcon className="mt-0.5 size-4 text-[#f59e0b]" aria-hidden />
                        )}
                        <div>
                          <p className="text-[13px] font-semibold text-[#111827]">{item.gateway_label}</p>
                          <p className="text-[12px] text-[#6b7280]">{item.detail_line}</p>
                        </div>
                      </div>
                      <GatewayBadge label={item.status_label} tone={item.status_tone} />
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