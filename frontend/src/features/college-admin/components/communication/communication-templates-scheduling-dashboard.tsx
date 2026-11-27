"use client";

import { CollegeAdminModulePageLayout } from "@/features/college-admin/components/layout/college-admin-module-page-layout";
import Link from "next/link";
import { useState, type ReactNode } from "react";

import { CollegeAdminPlusActionLabel } from "@/features/college-admin/components/ui/college-admin-plus-action";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useCommunicationTemplatesSchedulingPage } from "@/features/college-admin/hooks/use-communication-templates-scheduling";
import type {
  CommunicationScheduledMessagesPage,
  CommunicationTemplatesManagementPage,
  CommunicationTemplatesPagination,
} from "@/features/college-admin/types/communication-templates-scheduling";
import { cn } from "@/lib/utils";

const FIGMA: Record<Variant, string> = {
  templates: "161:9765",
  scheduled: "161:10068",
};

const PAGE_SIZE: Record<Variant, number> = {
  templates: 4,
  scheduled: 3,
};

type Variant = "templates" | "scheduled";

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
  pagination: CommunicationTemplatesPagination;
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

function TableShell({
  title,
  headers,
  footerLabel,
  pagination,
  onPage,
  emptyMessage,
  variant,
  children,
}: {
  title: string;
  headers: string[];
  footerLabel: string;
  pagination: CommunicationTemplatesPagination;
  onPage: (page: number) => void;
  emptyMessage: string;
  variant: Variant;
  children: ReactNode;
}) {
  const numericFrom = variant === "templates" ? 3 : 3;
  return (
    <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
      <div className="border-b border-[#f1f5f9] px-5 py-3.5">
        <h3 className="text-[14px] font-semibold text-[#111827]">{title}</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[52rem] text-left text-[13px]">
          <thead>
            <tr className="border-b border-[#f1f5f9] text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
              {headers.map((header, index, all) => (
                <th
                  key={header}
                  className={cn(
                    "pb-3 pt-4 font-medium",
                    index === 0 ? "pl-5 pr-3" : "pr-3",
                    index === all.length - 1 ? "pr-5" : "",
                    index >= numericFrom && variant === "templates" ? "text-right tabular-nums" : "",
                    index >= 3 && variant === "scheduled" ? "text-right" : "",
                    index === all.length - 1 ? "text-right" : "",
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

export function CommunicationTemplatesSchedulingDashboard({ variant }: { variant: Variant }) {
  const [page, setPage] = useState(1);
  const pageSize = PAGE_SIZE[variant];
  const { data, isLoading, isError, error, refetch, isFetching } = useCommunicationTemplatesSchedulingPage(
    variant,
    page,
    pageSize,
  );

  return (
    <CollegeAdminModulePageLayout figmaFrame={FIGMA[variant]}>
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">{data?.page_title ?? ""}</h2>
          {data?.page_subtitle ? <p className="mt-1 text-[14px] text-[#6b7280]">{data.page_subtitle}</p> : null}
        </div>
        {data ? (
          <Link
            href={data.primary_action_href}
            className="inline-flex h-9 shrink-0 items-center rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
          >
            <CollegeAdminPlusActionLabel label={data.primary_action_label} />
          </Link>
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
        <TableShell
          title={
            variant === "templates"
              ? (data as CommunicationTemplatesManagementPage).templates_section_title
              : (data as CommunicationScheduledMessagesPage).scheduled_section_title
          }
          headers={data.table_headers}
          footerLabel={data.count_footer_label || data.showing_label}
          pagination={data.pagination}
          onPage={setPage}
          emptyMessage={data.empty_table_message}
          variant={variant}
        >
          {variant === "templates" &&
            ((data as CommunicationTemplatesManagementPage).template_rows.length ? (
              (data as CommunicationTemplatesManagementPage).template_rows.map((row) => (
                <tr key={row.row_key} className="hover:bg-[#f9fafb]">
                  <td className="pl-5 py-3 pr-3 font-medium text-[#111827]">
                    <Link href={row.detail_href} className="hover:text-[#245dd8]">
                      {row.template_label}
                    </Link>
                  </td>
                  <td className="py-3 pr-3 text-[#6b7280]">{row.channel_label}</td>
                  <td className="py-3 pr-3 text-[#6b7280]">{row.language_label}</td>
                  <td className="py-3 pr-3 text-right tabular-nums">{row.variables_count}</td>
                  <td className="py-3 pr-3 text-right text-[#6b7280]">{row.updated_label}</td>
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
            ))}
          {variant === "scheduled" &&
            ((data as CommunicationScheduledMessagesPage).message_rows.length ? (
              (data as CommunicationScheduledMessagesPage).message_rows.map((row) => (
                <tr key={row.row_key} className="hover:bg-[#f9fafb]">
                  <td className="pl-5 py-3 pr-3 font-medium text-[#111827]">
                    <Link href={row.detail_href} className="hover:text-[#245dd8]">
                      {row.message_label}
                    </Link>
                  </td>
                  <td className="py-3 pr-3 text-[#6b7280]">{row.audience_label}</td>
                  <td className="py-3 pr-3 text-[#6b7280]">{row.channels_label}</td>
                  <td className="py-3 pr-3 text-right text-[#6b7280]">{row.send_at_label}</td>
                  <td className="py-3 pr-3 text-right text-[#6b7280]">{row.created_by_label}</td>
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
            ))}
        </TableShell>
      )}
    </CollegeAdminModulePageLayout>
  );
}

export function CommunicationTemplatesDashboard() {
  return <CommunicationTemplatesSchedulingDashboard variant="templates" />;
}

export function CommunicationScheduledMessagesDashboard() {
  return <CommunicationTemplatesSchedulingDashboard variant="scheduled" />;
}