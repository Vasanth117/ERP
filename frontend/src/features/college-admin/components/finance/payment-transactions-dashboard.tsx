"use client";

import { useEffect, useState } from "react";

import { SearchIcon } from "@/components/icons/erp/generated/search";
import { Button } from "@/components/ui/button";
import { CollegeAdminDownload } from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { FinancePaymentPagination, FinancePaymentStatusPill } from "@/features/college-admin/components/finance/finance-payment-ui";
import { FinancePaymentsSubNav } from "@/features/college-admin/components/finance/finance-payments-sub-nav";
import {
  CollegeAdminPanelEmptyState,
  CollegeAdminTablePanel,
} from "@/features/college-admin/components/ui/dashboard-panel-ui";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { usePaymentTransactionsPage } from "@/features/college-admin/hooks/use-payment-transactions-page";
import { cn } from "@/lib/utils";

function FilterSelect({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <select
      aria-label={label}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="h-9 min-w-[9rem] rounded-md border border-[#dce3ec] bg-white px-3 pr-8 text-[13px] text-[#374151]"
    >
      {options.map((opt) => (
        <option key={`${opt.value}-${opt.label}`} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  );
}

export function PaymentTransactionsDashboard() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [month, setMonth] = useState("");
  const [method, setMethod] = useState("all");
  const [status, setStatus] = useState("all");

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedSearch(search.trim()), 300);
    return () => window.clearTimeout(timer);
  }, [search]);

  useEffect(() => {
    setPage(1);
  }, [debouncedSearch, month, method, status]);

  const { data, isLoading, isError, error, refetch, isFetching } = usePaymentTransactionsPage({
    page,
    search: debouncedSearch || undefined,
    month: month || undefined,
    method: method === "all" ? undefined : method,
    status: status === "all" ? undefined : status,
  });

  useEffect(() => {
    if (data?.selected_month && !month) {
      setMonth(data.selected_month);
    }
  }, [data?.selected_month, month]);

  const handleExport = () => {
    if (!data?.transaction_rows.length) return;
    const blob = new Blob([JSON.stringify(data.transaction_rows, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "payment-transactions.json";
    anchor.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-5" data-figma-frame="finance-payments-all">
      {data?.sub_nav?.length ? <FinancePaymentsSubNav items={data.sub_nav} /> : null}

      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Payment Transactions"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">
            {data?.page_subtitle ?? "All verified, pending and failed payments"}
          </p>
        </div>
        <Button
          type="button"
          className="h-9 gap-1.5 bg-[#245dd8] text-xs font-medium hover:bg-[#1f4fb8]"
          onClick={handleExport}
          disabled={isLoading || !data?.transaction_rows.length}
        >
          <CollegeAdminDownload className="size-3.5" aria-hidden />
          {data?.export_label ?? "Export"}
        </Button>
      </div>

      <div className="flex flex-col gap-3 xl:flex-row xl:items-center">
        <div className="relative min-w-0 flex-1">
          <SearchIcon className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-[#9ca3af]" aria-hidden />
          <input
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={data?.search_placeholder ?? "Search transaction, student or invoice"}
            className="h-10 w-full rounded-md border border-[#dce3ec] bg-white pl-9 pr-3 text-[13px] text-[#374151]"
          />
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <FilterSelect
            label={data?.month_filter_label ?? "Month"}
            value={month || data?.selected_month || ""}
            onChange={setMonth}
            options={data?.month_options ?? []}
          />
          <FilterSelect
            label={data?.method_filter_label ?? "Method"}
            value={method}
            onChange={setMethod}
            options={data?.method_options ?? [{ value: "all", label: "All methods" }]}
          />
          <FilterSelect
            label={data?.status_filter_label ?? "Status"}
            value={status}
            onChange={setStatus}
            options={data?.status_options ?? [{ value: "all", label: "All statuses" }]}
          />
          {isFetching && !isLoading ? <span className="text-[12px] text-[#9ca3af]">Updating…</span> : null}
        </div>
      </div>

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <CollegeAdminTablePanel
            title={data.transactions_section_title}
            footer={
              <>
                <span>{data.showing_label}</span>
                {data.pagination.total_pages > 0 ? (
                  <FinancePaymentPagination pagination={data.pagination} page={page} setPage={setPage} />
                ) : null}
              </>
            }
          >
            {data.transaction_rows.length ? (
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
                          )}
                        >
                          {header}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#f1f5f9]">
                    {data.transaction_rows.map((row) => (
                      <tr key={row.transaction_id} className="transition-colors hover:bg-[#f8fafc]">
                        <td className="px-5 py-3.5 font-mono text-[12px] font-medium text-[#111827]">
                          {row.transaction_id}
                        </td>
                        <td className="py-3.5 pr-3 text-[#374151]">{row.student_name}</td>
                        <td className="py-3.5 pr-3 text-[12px] text-[#6b7280]">{row.invoice_label}</td>
                        <td className="py-3.5 pr-3 text-[#374151]">{row.method_label}</td>
                        <td className="py-3.5 pr-3 tabular-nums font-medium text-[#111827]">{row.amount_label}</td>
                        <td className="py-3.5 pr-5 text-right">
                          <FinancePaymentStatusPill label={row.status_label} tone={row.status_tone} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <CollegeAdminPanelEmptyState title="No transactions match your filters" />
            )}
          </CollegeAdminTablePanel>
        ) : null}
      </QueryState>
    </div>
  );
}