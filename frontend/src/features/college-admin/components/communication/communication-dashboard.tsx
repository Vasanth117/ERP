"use client";

import { CollegeAdminModulePageLayout } from "@/features/college-admin/components/layout/college-admin-module-page-layout";
import { CollegeAdminModulePageHeading } from "@/features/college-admin/components/layout/college-admin-module-page-heading";
import Link from "next/link";
import { useMemo, useState, type ReactNode } from "react";

import { CollegeAdminPlusActionLabel } from "@/features/college-admin/components/ui/college-admin-plus-action";
import {
  getCollegeAdminErpIcon,
  resolveCollegeAdminIconSlug,
} from "@/features/college-admin/components/layout/college-admin-erp-icons";
import {
  CollegeAdminKpiGrid,
  CollegeAdminUserDashboardKpiCard,
} from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useCommunicationDashboardPage } from "@/features/college-admin/hooks/use-communication-dashboard";
import type {
  CommunicationChannelSidebarItem,
  CommunicationDashboardPage,
  CommunicationDashboardPagination,
} from "@/features/college-admin/types/communication-dashboard";
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

function TablePagination({
  pagination,
  onPage,
}: {
  pagination: CommunicationDashboardPagination;
  onPage: (page: number) => void;
}) {
  if (pagination.total_pages <= 0) return null;
  return (
    <nav className="flex flex-wrap items-center justify-end gap-1" aria-label="Deliveries pagination">
      <button
        type="button"
        className="rounded border border-[#dce3ec] px-2 py-1 text-[12px] disabled:opacity-40"
        disabled={!pagination.has_previous}
        onClick={() => onPage(Math.max(1, pagination.page - 1))}
      >
        Prev
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
        Next
      </button>
    </nav>
  );
}

function ChannelRow({ item }: { item: CommunicationChannelSidebarItem }) {
  const slug = resolveCollegeAdminIconSlug(item.icon_key);
  const Icon = getCollegeAdminErpIcon(slug);
  return (
    <li className="flex items-center justify-between gap-3 border-b border-[#f1f5f9] py-3.5 last:border-0">
      <ButtonLink href={item.href} className="flex min-w-0 flex-1 items-center gap-3">
        {Icon ? (
          <Icon className="size-[18px] shrink-0 text-[#9ca3af]" aria-hidden />
        ) : (
          <span className="size-[18px] shrink-0 rounded bg-[#f3f4f6]" aria-hidden />
        )}
        <div className="min-w-0 text-left">
          <p className="text-[13px] font-medium text-[#111827]">{item.title}</p>
          <p className="text-[12px] text-[#6b7280]">{item.subtitle_line}</p>
        </div>
      </ButtonLink>
      <StatusPill label={item.status_label} tone={item.status_tone} />
    </li>
  );
}

function ButtonLink({
  href,
  className,
  children,
}: {
  href: string;
  className?: string;
  children: ReactNode;
}) {
  return (
    <Link href={href} className={cn("hover:opacity-90", className)}>
      {children}
    </Link>
  );
}

const emptyPagination: CommunicationDashboardPagination = {
  page: 1,
  page_size: 3,
  total: 0,
  total_pages: 0,
  page_numbers: [],
  has_previous: false,
  has_next: false,
};

function mergeView(data: CommunicationDashboardPage | undefined) {
  return {
    page_title: data?.page_title ?? "",
    page_subtitle: data?.page_subtitle ?? "",
    create_announcement_label: data?.create_announcement_label ?? "",
    create_announcement_href: data?.create_announcement_href ?? "#",
    kpis: data?.kpis ?? [],
    deliveries_section_title: data?.deliveries_section_title ?? "",
    table_headers: data?.table_headers ?? [],
    delivery_rows: data?.delivery_rows ?? [],
    empty_table_message: data?.empty_table_message ?? "",
    showing_label: data?.showing_label ?? "",
    pagination: data?.pagination ?? emptyPagination,
    channels_section_title: data?.channels_section_title ?? "",
    channel_items: data?.channel_items ?? [],
  };
}

export function CommunicationDashboard() {
  const [page, setPage] = useState(1);
  const queryParams = useMemo(() => ({ page, page_size: 3 }), [page]);
  const { data, isLoading, isError, error, refetch, isFetching } = useCommunicationDashboardPage(queryParams);
  const view = mergeView(data);

  return (
    <CollegeAdminModulePageLayout figmaFrame="161:6942">
      <CollegeAdminModulePageHeading
        title={view.page_title || "Communication Dashboard"}
        subtitle={view.page_subtitle || undefined}
        actions={
          <Link
            href={view.create_announcement_href}
            className="inline-flex h-9 shrink-0 items-center rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
          >
            <CollegeAdminPlusActionLabel label={view.create_announcement_label || "Create announcement"} />
          </Link>
        }
      />

      {isLoading || isFetching ? (
        <p className="text-[12px] text-[#9ca3af]">{isLoading ? "Loading communication data…" : "Updating…"}</p>
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

          {!data ? null : (
            <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_280px]">
              <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                  <h3 className="text-[14px] font-semibold text-[#111827]">
                    {view.deliveries_section_title || "Deliveries"}
                  </h3>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[52rem] text-left text-[13px]">
                    <thead>
                      <tr className="border-b border-[#f1f5f9] text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                        {view.table_headers.map((header, index, headers) => (
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
                      {view.delivery_rows.length ? (
                        view.delivery_rows.map((row) => (
                          <tr key={row.batch_key} className="text-[#374151] hover:bg-[#f9fafb]">
                            <td className="max-w-[14rem] truncate pl-5 py-3 pr-3 font-medium text-[#111827]">
                              <Link href={row.detail_href} className="hover:text-[#245dd8]">
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
                            colSpan={Math.max(view.table_headers.length, 1)}
                            className="px-5 py-10 text-center text-sm text-[#9ca3af]"
                          >
                            {view.empty_table_message}
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
                <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
                  <span>{view.showing_label}</span>
                  <TablePagination
                    pagination={view.pagination}
                    onPage={(p) => {
                      setPage(p);
                    }}
                  />
                </div>
              </section>

              <section className="h-fit overflow-hidden rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <h3 className="mb-2 text-[14px] font-semibold text-[#111827]">
                  {view.channels_section_title || "Channels"}
                </h3>
                <ul>
                  {view.channel_items.map((item) => (
                    <ChannelRow key={item.channel_key} item={item} />
                  ))}
                </ul>
              </section>
            </div>
          )}
        </>
      )}
    </CollegeAdminModulePageLayout>
  );
}