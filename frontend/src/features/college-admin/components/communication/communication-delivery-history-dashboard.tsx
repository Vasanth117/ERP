"use client";

import { CollegeAdminModulePageLayout } from "@/features/college-admin/components/layout/college-admin-module-page-layout";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { SearchIcon } from "@/components/icons/erp/generated/search";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { CollegeAdminDownload } from "@/features/college-admin/components/layout/college-admin-erp-icons";
import {
  CollegeAdminKpiGrid,
  CollegeAdminUserDashboardKpiCard,
} from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { downloadCommunicationHistoryExport } from "@/features/college-admin/api/communication-delivery-history";
import {
  useCommunicationDeliveryHistoryPage,
  useRetryCommunicationFailedDeliveries,
} from "@/features/college-admin/hooks/use-communication-delivery-history";
import type {
  CommunicationDeliveryPagination,
  CommunicationDeliveryStatusPage,
  CommunicationHistoryPage,
} from "@/features/college-admin/types/communication-delivery-history";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";
import { cn } from "@/lib/utils";

const FIGMA: Record<Variant, string> = {
  delivery: "161:10356",
  history: "161:10679",
};

type Variant = "delivery" | "history";

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

function TablePagination({
  pagination,
  onPage,
}: {
  pagination: CommunicationDeliveryPagination;
  onPage: (page: number) => void;
}) {
  if (pagination.total_pages <= 0) return null;
  return (
    <nav className="flex flex-wrap items-center justify-end gap-1" aria-label="Pagination">
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
      className="h-9 min-w-[8.5rem] rounded-md border border-[#dce3ec] bg-white px-3 text-[13px] text-[#374151]"
    >
      {options.map((opt) => (
        <option key={`${opt.value}-${opt.label}`} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  );
}

export function CommunicationDeliveryHistoryDashboard({ variant }: { variant: Variant }) {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [month, setMonth] = useState("");
  const [channel, setChannel] = useState("");
  const [sender, setSender] = useState("");
  const [exportPending, setExportPending] = useState(false);

  const queryClient = useQueryClient();
  const retryMutation = useRetryCommunicationFailedDeliveries();

  useEffect(() => {
    if (variant !== "history") return undefined;
    const timer = window.setTimeout(() => setDebouncedSearch(search.trim()), 300);
    return () => window.clearTimeout(timer);
  }, [search, variant]);

  useEffect(() => {
    setPage(1);
  }, [debouncedSearch, month, channel, sender, variant]);

  const queryParams = useMemo(() => {
    if (variant === "delivery") {
      return { page, page_size: 3 };
    }
    return {
      page,
      page_size: 4,
      search: debouncedSearch || undefined,
      month: month || undefined,
      channel: channel || undefined,
      sender: sender || undefined,
    };
  }, [variant, page, debouncedSearch, month, channel, sender]);

  const { data, isLoading, isError, error, refetch, isFetching } = useCommunicationDeliveryHistoryPage(
    variant,
    queryParams,
  );

  useEffect(() => {
    if (variant !== "history" || month || !data) return;
    const history = data as CommunicationHistoryPage;
    if (history.month_options.length) {
      setMonth(history.month_options[0].value);
    }
  }, [data, month, variant]);

  const handleRetry = useCallback(() => {
    retryMutation.mutate(undefined, {
      onSuccess: () => {
        void queryClient.invalidateQueries({ queryKey: collegeAdminQueryKeys.communicationDeliveryStatusPage() });
      },
    });
  }, [queryClient, retryMutation]);

  const handleExport = useCallback(async () => {
    if (variant !== "history") return;
    setExportPending(true);
    try {
      await downloadCommunicationHistoryExport({
        search: debouncedSearch || undefined,
        month: month || undefined,
        channel: channel || undefined,
        sender: sender || undefined,
      });
    } finally {
      setExportPending(false);
    }
  }, [variant, debouncedSearch, month, channel, sender]);

  const deliveryData = variant === "delivery" ? (data as CommunicationDeliveryStatusPage | undefined) : undefined;
  const historyData = variant === "history" ? (data as CommunicationHistoryPage | undefined) : undefined;

  return (
    <CollegeAdminModulePageLayout figmaFrame={FIGMA[variant]}>
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">{data?.page_title ?? ""}</h2>
          {data?.page_subtitle ? <p className="mt-1 text-[14px] text-[#6b7280]">{data.page_subtitle}</p> : null}
        </div>
        {deliveryData ? (
          <Button
            type="button"
            className="h-9 gap-1.5 bg-[#245dd8] text-xs font-medium text-white hover:bg-[#1f4fb8]"
            disabled={!deliveryData.retry_enabled || retryMutation.isPending}
            onClick={handleRetry}
          >
            ↻ {deliveryData.retry_action_label}
          </Button>
        ) : historyData ? (
          <Button
            type="button"
            className="h-9 gap-1.5 bg-[#245dd8] text-xs font-medium text-white hover:bg-[#1f4fb8]"
            disabled={exportPending || isLoading}
            onClick={() => void handleExport()}
          >
            <CollegeAdminDownload className="size-3.5" aria-hidden />
            {historyData.export_label}
          </Button>
        ) : null}
      </div>

      {isLoading || isFetching ? (
        <p className="text-[12px] text-[#9ca3af]">{isLoading ? "Loading…" : "Updating…"}</p>
      ) : null}

      {isError ? (
        <QueryState isError={isError} error={error} onRetry={() => void refetch()}>
          <></>
        </QueryState>
      ) : !data ? null : (
        <>
          {deliveryData ? (
            <>
              <CollegeAdminKpiGrid>
                {deliveryData.kpis.map((kpi, index) => (
                  <CollegeAdminUserDashboardKpiCard key={kpi.key} kpi={kpi} index={index} />
                ))}
              </CollegeAdminKpiGrid>
              <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                  <h3 className="text-[14px] font-semibold text-[#111827]">{deliveryData.deliveries_section_title}</h3>
                </div>
                <DeliveryTable data={deliveryData} onPage={setPage} />
              </section>
            </>
          ) : null}

          {historyData ? (
            <>
              <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
                <div className="relative min-w-[14rem] flex-1 sm:max-w-md">
                  <SearchIcon className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-[#9ca3af]" />
                  <Input
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder={historyData.search_placeholder}
                    className="h-9 border-[#dce3ec] pl-9 text-[13px]"
                  />
                </div>
                <FilterSelect
                  label="Month"
                  value={month}
                  onChange={setMonth}
                  options={historyData.month_options}
                />
                <FilterSelect
                  label={historyData.channel_filter_label}
                  value={channel}
                  onChange={setChannel}
                  options={historyData.channel_options}
                />
                <FilterSelect
                  label={historyData.sender_filter_label}
                  value={sender}
                  onChange={setSender}
                  options={historyData.sender_options}
                />
              </div>

              <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                  <h3 className="text-[14px] font-semibold text-[#111827]">
                    {historyData.announcements_section_title}
                  </h3>
                </div>
                <HistoryTable data={historyData} onPage={setPage} />
              </section>
            </>
          ) : null}
        </>
      )}
    </CollegeAdminModulePageLayout>
  );
}

function DeliveryTable({
  data,
  onPage,
}: {
  data: CommunicationDeliveryStatusPage;
  onPage: (p: number) => void;
}) {
  return (
    <>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[48rem] text-left text-[13px]">
          <thead>
            <tr className="border-b border-[#f1f5f9] text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
              {data.table_headers.map((header, index, headers) => (
                <th
                  key={header}
                  className={cn(
                    "pb-3 pt-4 font-medium",
                    index === 0 ? "pl-5 pr-3" : "pr-3",
                    index === headers.length - 1 ? "pr-5" : "",
                    index >= 2 ? "text-right tabular-nums" : "",
                  )}
                >
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-[#f1f5f9]">
            {data.delivery_rows.length ? (
              data.delivery_rows.map((row) => (
                <tr key={row.batch_key} className="hover:bg-[#f9fafb]">
                  <td className="pl-5 py-3 pr-3 font-medium text-[#245dd8]">
                    <Link href={row.detail_href} className="hover:underline">
                      {row.message_label}
                    </Link>
                  </td>
                  <td className="py-3 pr-3 text-[#6b7280]">{row.channel_label}</td>
                  <td className="py-3 pr-3 text-right tabular-nums">{row.recipients_count.toLocaleString("en-IN")}</td>
                  <td className="py-3 pr-3 text-right tabular-nums">{row.delivered_count.toLocaleString("en-IN")}</td>
                  <td className="py-3 pr-3 text-right tabular-nums">{row.failed_count.toLocaleString("en-IN")}</td>
                  <td className="py-3 pr-5 text-right">
                    <StatusPill label={row.status_label} tone={row.status_tone} />
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td
                  colSpan={Math.max(data.table_headers.length, 1)}
                  className="px-5 py-10 text-center text-sm text-[#9ca3af]"
                >
                  {data.empty_table_message}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
        <span>{data.count_footer_label || data.showing_label}</span>
        <TablePagination pagination={data.pagination} onPage={onPage} />
      </div>
    </>
  );
}

function HistoryTable({
  data,
  onPage,
}: {
  data: CommunicationHistoryPage;
  onPage: (p: number) => void;
}) {
  return (
    <>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[52rem] text-left text-[13px]">
          <thead>
            <tr className="border-b border-[#f1f5f9] text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
              {data.table_headers.map((header, index, headers) => (
                <th
                  key={header}
                  className={cn(
                    "pb-3 pt-4 font-medium",
                    index === 0 ? "pl-5 pr-3" : "pr-3",
                    index === headers.length - 1 ? "pr-5" : "",
                    index >= 3 ? "text-right tabular-nums" : "",
                  )}
                >
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-[#f1f5f9]">
            {data.announcement_rows.length ? (
              data.announcement_rows.map((row) => (
                <tr key={row.announcement_id} className="hover:bg-[#f9fafb]">
                  <td className="max-w-[16rem] truncate pl-5 py-3 pr-3 font-medium text-[#245dd8]">
                    <Link href={row.detail_href} className="hover:underline">
                      {row.title}
                    </Link>
                  </td>
                  <td className="py-3 pr-3 text-[#6b7280]">{row.audience_label}</td>
                  <td className="py-3 pr-3 text-[#6b7280]">{row.channels_label}</td>
                  <td className="py-3 pr-3 text-right tabular-nums text-[#6b7280]">{row.published_label}</td>
                  <td className="py-3 pr-3 text-right tabular-nums">{row.reach_label}</td>
                  <td className="py-3 pr-5 text-right">
                    <StatusPill label={row.status_label} tone={row.status_tone} />
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td
                  colSpan={Math.max(data.table_headers.length, 1)}
                  className="px-5 py-10 text-center text-sm text-[#9ca3af]"
                >
                  {data.empty_table_message}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
        <span>{data.count_footer_label || data.showing_label}</span>
        <TablePagination pagination={data.pagination} onPage={onPage} />
      </div>
    </>
  );
}

export function CommunicationDeliveryStatusDashboard() {
  return <CommunicationDeliveryHistoryDashboard variant="delivery" />;
}

export function CommunicationHistoryDashboard() {
  return <CommunicationDeliveryHistoryDashboard variant="history" />;
}