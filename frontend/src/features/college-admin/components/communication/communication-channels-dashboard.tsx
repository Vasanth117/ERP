"use client";

import { CollegeAdminModulePageLayout } from "@/features/college-admin/components/layout/college-admin-module-page-layout";
import Link from "next/link";
import { useState, type ReactNode } from "react";

import { CollegeAdminPlusActionLabel } from "@/features/college-admin/components/ui/college-admin-plus-action";
import {
  CollegeAdminKpiGrid,
  CollegeAdminUserDashboardKpiCard,
} from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useCommunicationChannelPage } from "@/features/college-admin/hooks/use-communication-channels";
import type {
  CommunicationChannelPagination,
  CommunicationEmailChannelPage,
  CommunicationSmsChannelPage,
  CommunicationWhatsappChannelPage,
} from "@/features/college-admin/types/communication-channels";
import { cn } from "@/lib/utils";

const FIGMA: Record<ChannelVariant, string> = {
  email: "161:8858",
  sms: "161:9163",
  whatsapp: "161:9468",
};

type ChannelVariant = "email" | "sms" | "whatsapp";

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
  pagination: CommunicationChannelPagination;
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

function ChannelPrimaryAction({
  href,
  label,
  style,
}: {
  href: string;
  label: string;
  style: string;
}) {
  if (style === "link") {
    return (
      <Link
        href={href}
        className="inline-flex h-9 shrink-0 items-center gap-1 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
      >
        {label}
        <span aria-hidden className="text-[14px]">
          ›
        </span>
      </Link>
    );
  }
  return (
    <Link
      href={href}
      className="inline-flex h-9 shrink-0 items-center rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
    >
      <CollegeAdminPlusActionLabel label={label} />
    </Link>
  );
}

function AlertBanner({
  tone,
  message,
  linkLabel,
  linkHref,
}: {
  tone: string;
  message: string;
  linkLabel: string;
  linkHref: string;
}) {
  const bg = tone === "warning" ? "bg-[#fffbeb] border-[#fde68a]" : "bg-[#eff6ff] border-[#bfdbfe]";
  return (
    <div className={cn("flex flex-col gap-2 rounded-lg border px-4 py-3 text-[13px] sm:flex-row sm:items-center sm:justify-between", bg)}>
      <p className="text-[#92400e]">{message}</p>
      <Link href={linkHref} className="shrink-0 font-medium text-[#245dd8] hover:underline">
        {linkLabel} →
      </Link>
    </div>
  );
}

function ChannelTableSection({
  title,
  headers,
  footerLabel,
  pagination,
  onPage,
  emptyMessage,
  children,
}: {
  title: string;
  headers: string[];
  footerLabel: string;
  pagination: CommunicationChannelPagination;
  onPage: (page: number) => void;
  emptyMessage: string;
  children: ReactNode;
}) {
  return (
    <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
      <div className="border-b border-[#f1f5f9] px-5 py-3.5">
        <h3 className="text-[14px] font-semibold text-[#111827]">{title}</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[48rem] text-left text-[13px]">
          <thead>
            <tr className="border-b border-[#f1f5f9] text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
              {headers.map((header, index, all) => (
                <th
                  key={header}
                  className={cn(
                    "pb-3 pt-4 font-medium",
                    index === 0 ? "pl-5 pr-3" : "pr-3",
                    index === all.length - 1 ? "pr-5" : "",
                    index >= 2 ? "text-right tabular-nums" : "",
                  )}
                >
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-[#f1f5f9]">{children}</tbody>
        </table>
      </div>
      <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
        <span>{footerLabel}</span>
        <TablePagination pagination={pagination} onPage={onPage} />
      </div>
    </section>
  );
}

function EmptyRow({ colSpan, message }: { colSpan: number; message: string }) {
  return (
    <tr>
      <td colSpan={colSpan} className="px-5 py-10 text-center text-sm text-[#9ca3af]">
        {message}
      </td>
    </tr>
  );
}

export function CommunicationChannelsDashboard({ variant }: { variant: ChannelVariant }) {
  const [page, setPage] = useState(1);
  const { data, isLoading, isError, error, refetch, isFetching } = useCommunicationChannelPage(variant, page);

  const actionStyle =
    variant === "whatsapp"
      ? ((data as CommunicationWhatsappChannelPage | undefined)?.primary_action_style ?? "link")
      : "button";

  const alert =
    variant === "whatsapp" ? (data as CommunicationWhatsappChannelPage | undefined)?.alert_banner : null;

  return (
    <CollegeAdminModulePageLayout figmaFrame={FIGMA[variant]}>
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">{data?.page_title ?? ""}</h2>
          {data?.page_subtitle ? <p className="mt-1 text-[14px] text-[#6b7280]">{data.page_subtitle}</p> : null}
        </div>
        {data ? (
          <ChannelPrimaryAction
            href={data.primary_action_href}
            label={data.primary_action_label}
            style={actionStyle}
          />
        ) : null}
      </div>

      {alert ? (
        <AlertBanner
          tone={alert.tone}
          message={alert.message}
          linkLabel={alert.link_label}
          linkHref={alert.link_href}
        />
      ) : null}

      {isLoading || isFetching ? (
        <p className="text-[12px] text-[#9ca3af]">{isLoading ? "Loading…" : "Updating…"}</p>
      ) : null}

      {isError ? (
        <QueryState isError={isError} error={error} onRetry={() => void refetch()}>
          <></>
        </QueryState>
      ) : (
        <>
          <CollegeAdminKpiGrid>
            {(data?.kpis ?? []).map((kpi, index) => (
              <CollegeAdminUserDashboardKpiCard key={kpi.key} kpi={kpi} index={index} />
            ))}
          </CollegeAdminKpiGrid>

          {!data ? null : variant === "email" ? (
            <ChannelTableSection
              title={(data as CommunicationEmailChannelPage).campaigns_section_title}
              headers={data.table_headers}
              footerLabel={data.count_footer_label || data.showing_label}
              pagination={data.pagination}
              onPage={setPage}
              emptyMessage={data.empty_table_message}
            >
              {(data as CommunicationEmailChannelPage).campaign_rows.length ? (
                (data as CommunicationEmailChannelPage).campaign_rows.map((row) => (
                  <tr key={row.row_key} className="hover:bg-[#f9fafb]">
                    <td className="pl-5 py-3 pr-3 font-medium text-[#245dd8]">
                      <Link href={row.detail_href} className="hover:underline">
                        {row.campaign_label}
                      </Link>
                    </td>
                    <td className="py-3 pr-3 text-[#6b7280]">{row.audience_label}</td>
                    <td className="py-3 pr-3 text-right text-[#6b7280]">{row.sent_label}</td>
                    <td className="py-3 pr-3 text-right tabular-nums">{row.opened_label}</td>
                    <td className="py-3 pr-3 text-right tabular-nums">{row.bounced_count.toLocaleString("en-IN")}</td>
                    <td className="py-3 pr-5 text-right">
                      <StatusPill label={row.status_label} tone={row.status_tone} />
                    </td>
                  </tr>
                ))
              ) : (
                <EmptyRow colSpan={Math.max(data.table_headers.length, 1)} message={data.empty_table_message} />
              )}
            </ChannelTableSection>
          ) : variant === "sms" ? (
            <ChannelTableSection
              title={(data as CommunicationSmsChannelPage).batches_section_title}
              headers={data.table_headers}
              footerLabel={data.count_footer_label || data.showing_label}
              pagination={data.pagination}
              onPage={setPage}
              emptyMessage={data.empty_table_message}
            >
              {(data as CommunicationSmsChannelPage).batch_rows.length ? (
                (data as CommunicationSmsChannelPage).batch_rows.map((row) => (
                  <tr key={row.row_key} className="hover:bg-[#f9fafb]">
                    <td className="pl-5 py-3 pr-3 font-medium text-[#111827]">{row.batch_label}</td>
                    <td className="py-3 pr-3 text-[#6b7280]">{row.template_label}</td>
                    <td className="py-3 pr-3 text-right tabular-nums">{row.recipients_count.toLocaleString("en-IN")}</td>
                    <td className="py-3 pr-3 text-right tabular-nums">{row.delivered_count.toLocaleString("en-IN")}</td>
                    <td className="py-3 pr-3 text-right tabular-nums">{row.failed_count.toLocaleString("en-IN")}</td>
                    <td className="py-3 pr-5 text-right">
                      <StatusPill label={row.status_label} tone={row.status_tone} />
                    </td>
                  </tr>
                ))
              ) : (
                <EmptyRow colSpan={Math.max(data.table_headers.length, 1)} message={data.empty_table_message} />
              )}
            </ChannelTableSection>
          ) : (
            <ChannelTableSection
              title={(data as CommunicationWhatsappChannelPage).templates_section_title}
              headers={data.table_headers}
              footerLabel={data.count_footer_label || data.showing_label}
              pagination={data.pagination}
              onPage={setPage}
              emptyMessage={data.empty_table_message}
            >
              {(data as CommunicationWhatsappChannelPage).template_rows.length ? (
                (data as CommunicationWhatsappChannelPage).template_rows.map((row) => (
                  <tr key={row.row_key} className="hover:bg-[#f9fafb]">
                    <td className="pl-5 py-3 pr-3 font-medium text-[#111827]">
                      <Link href={row.detail_href} className="hover:text-[#245dd8]">
                        {row.template_label}
                      </Link>
                    </td>
                    <td className="py-3 pr-3 text-right text-[#6b7280]">{row.category_label}</td>
                    <td className="py-3 pr-3 text-right text-[#6b7280]">{row.language_label}</td>
                    <td className="py-3 pr-5 text-right">
                      <StatusPill label={row.status_label} tone={row.status_tone} />
                    </td>
                  </tr>
                ))
              ) : (
                <EmptyRow colSpan={Math.max(data.table_headers.length, 1)} message={data.empty_table_message} />
              )}
            </ChannelTableSection>
          )}
        </>
      )}
    </CollegeAdminModulePageLayout>
  );
}

export function CommunicationEmailChannelDashboard() {
  return <CommunicationChannelsDashboard variant="email" />;
}

export function CommunicationSmsChannelDashboard() {
  return <CommunicationChannelsDashboard variant="sms" />;
}

export function CommunicationWhatsappChannelDashboard() {
  return <CommunicationChannelsDashboard variant="whatsapp" />;
}