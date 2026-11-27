"use client";

import { CollegeAdminModulePageLayout } from "@/features/college-admin/components/layout/college-admin-module-page-layout";
import Link from "next/link";
import { useMemo, useState } from "react";

import { CollegeAdminPlusActionLabel } from "@/features/college-admin/components/ui/college-admin-plus-action";
import {
  CollegeAdminKpiGrid,
  CollegeAdminUserDashboardKpiCard,
} from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useCommunicationFacultyNotificationsPage,
  useCommunicationParentCommunicationPage,
  useCommunicationStudentNotificationsPage,
} from "@/features/college-admin/hooks/use-communication-audience-notifications";
import type { CommunicationAudiencePagination } from "@/features/college-admin/types/communication-audience-notifications";
import { cn } from "@/lib/utils";

const FIGMA: Record<string, string> = {
  students: "161:7956",
  faculty: "161:8276",
  parents: "161:8567",
};

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
  pagination: CommunicationAudiencePagination;
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

type AudienceVariant = "students" | "faculty" | "parents";

function useAudiencePage(variant: AudienceVariant, page: number) {
  const params = useMemo(() => ({ page, page_size: 3 }), [page]);
  const student = useCommunicationStudentNotificationsPage(params, variant === "students");
  const faculty = useCommunicationFacultyNotificationsPage(params, variant === "faculty");
  const parent = useCommunicationParentCommunicationPage(params, variant === "parents");
  if (variant === "faculty") return faculty;
  if (variant === "parents") return parent;
  return student;
}

export function CommunicationAudienceNotificationsDashboard({ variant }: { variant: AudienceVariant }) {
  const [page, setPage] = useState(1);
  const { data, isLoading, isError, error, refetch, isFetching } = useAudiencePage(variant, page);

  const actionLabel =
    variant === "parents"
      ? (data as { new_message_label?: string })?.new_message_label ?? "New message"
      : (data as { new_notification_label?: string })?.new_notification_label ?? "New notification";
  const actionHref =
    variant === "parents"
      ? (data as { new_message_href?: string })?.new_message_href ?? "#"
      : (data as { new_notification_href?: string })?.new_notification_href ?? "#";

  const sectionTitle =
    variant === "students"
      ? (data as { deliveries_section_title?: string })?.deliveries_section_title ?? "Deliveries"
      : (data as { recent_section_title?: string })?.recent_section_title ?? "Recent";

  return (
    <CollegeAdminModulePageLayout figmaFrame={FIGMA[variant]}>
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">{data?.page_title ?? ""}</h2>
          {data?.page_subtitle ? (
            <p className="mt-1 text-[14px] text-[#6b7280]">{data.page_subtitle}</p>
          ) : null}
        </div>
        <Link
          href={actionHref}
          className="inline-flex h-9 shrink-0 items-center rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
        >
          <CollegeAdminPlusActionLabel label={actionLabel} />
        </Link>
      </div>

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

          {!data ? null : (
            <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                <h3 className="text-[14px] font-semibold text-[#111827]">{sectionTitle}</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[48rem] text-left text-[13px]">
                  <thead>
                    <tr className="border-b border-[#f1f5f9] text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                      {(data.table_headers ?? []).map((header, index, headers) => (
                        <th
                          key={header}
                          className={cn(
                            "pb-3 pt-4 font-medium",
                            index === 0 ? "pl-5 pr-3" : "pr-3",
                            index === headers.length - 1 ? "pr-5" : "",
                            index >= 2 && variant === "students" ? "text-right tabular-nums" : "",
                            index >= 2 && variant !== "students" ? "text-right" : "",
                          )}
                        >
                          {header}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#f1f5f9]">
                    {variant === "students" &&
                      ("delivery_rows" in data && data.delivery_rows.length ? (
                        data.delivery_rows.map((row) => (
                          <tr key={row.row_key} className="hover:bg-[#f9fafb]">
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
                      ))}
                    {variant === "faculty" &&
                      ("notification_rows" in data && data.notification_rows.length ? (
                        data.notification_rows.map((row) => (
                          <tr key={row.row_key} className="hover:bg-[#f9fafb]">
                            <td className="pl-5 py-3 pr-3 font-medium text-[#111827]">
                              <Link href={row.detail_href} className="hover:text-[#245dd8]">
                                {row.notification_label}
                              </Link>
                            </td>
                            <td className="py-3 pr-3 text-[#6b7280]">{row.audience_label}</td>
                            <td className="py-3 pr-3 text-right tabular-nums text-[#6b7280]">{row.sent_label}</td>
                            <td className="py-3 pr-3 text-right text-[#6b7280]">{row.read_label}</td>
                            <td className="py-3 pr-5 text-right text-[#6b7280]">{row.acknowledged_label}</td>
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
                    {variant === "parents" &&
                      ("message_rows" in data && data.message_rows.length ? (
                        data.message_rows.map((row) => (
                          <tr key={row.row_key} className="hover:bg-[#f9fafb]">
                            <td className="pl-5 py-3 pr-3 font-medium text-[#111827]">
                              <Link href={row.detail_href} className="hover:text-[#245dd8]">
                                {row.message_label}
                              </Link>
                            </td>
                            <td className="py-3 pr-3 text-[#6b7280]">{row.audience_label}</td>
                            <td className="py-3 pr-3 text-[#6b7280]">{row.channel_label}</td>
                            <td className="py-3 pr-3 text-right tabular-nums text-[#6b7280]">{row.sent_label}</td>
                            <td className="py-3 pr-5 text-right text-[#6b7280]">{row.delivered_label}</td>
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
                  </tbody>
                </table>
              </div>
              <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
                <span>
                  {"count_footer_label" in data && data.count_footer_label
                    ? data.count_footer_label
                    : data.showing_label}
                </span>
                <TablePagination pagination={data.pagination} onPage={setPage} />
              </div>
            </section>
          )}
        </>
      )}
    </CollegeAdminModulePageLayout>
  );
}

export function CommunicationStudentNotificationsDashboard() {
  return <CommunicationAudienceNotificationsDashboard variant="students" />;
}

export function CommunicationFacultyNotificationsDashboard() {
  return <CommunicationAudienceNotificationsDashboard variant="faculty" />;
}

export function CommunicationParentCommunicationDashboard() {
  return <CommunicationAudienceNotificationsDashboard variant="parents" />;
}