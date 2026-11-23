"use client";
import { CollegeAdminPlusActionLabel } from "@/features/college-admin/components/ui/college-admin-plus-action";

import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { SendIcon } from "@/components/icons/erp/generated/send";
import { YearsSemestersSubNav } from "@/features/college-admin/components/academics/years-semesters-sub-nav";
import {
  CollegeAdminPrimaryLink,
  CollegeAdminSecondaryButton,
} from "@/features/college-admin/components/ui/college-admin-action-button";
import { CollegeAdminSectionNav } from "@/features/college-admin/components/ui/college-admin-section-nav";
import {
  CollegeAdminPanelEmptyState,
  CollegeAdminSidePanel,
  CollegeAdminTablePanel,
} from "@/features/college-admin/components/ui/dashboard-panel-ui";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useAcademicCalendarConfigurationPage,
  usePublishAcademicCalendarConfiguration,
} from "@/features/college-admin/hooks/use-academic-calendar-configuration";
import type { AcademicCalendarConfigurationPage } from "@/features/college-admin/types/academic-calendar-configuration";
import { cn } from "@/lib/utils";

function StatusPill({ label, tone }: { label: string; tone: string }) {
  const styles: Record<string, string> = {
    success: "bg-[#ecfdf5] text-[#047857]",
    warning: "bg-[#fff7ed] text-[#c2410c]",
    info: "bg-[#eff6ff] text-[#1d4ed8]",
    muted: "bg-[#f3f4f6] text-[#6b7280]",
  };
  const key = tone in styles ? tone : "muted";
  return (
    <span className={cn("inline-flex rounded-full px-2.5 py-0.5 text-[11px] font-medium", styles[key])}>
      {label}
    </span>
  );
}

export function AcademicCalendarConfigurationDashboard() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const initialView = searchParams.get("view") ?? "list";
  const initialPage = Number(searchParams.get("page") ?? "1");

  const [view, setView] = useState(initialView);
  const [page, setPage] = useState(Number.isFinite(initialPage) && initialPage > 0 ? initialPage : 1);
  const [yearId, setYearId] = useState<string | undefined>();
  const [termId, setTermId] = useState<string | undefined>();

  const queryParams = useMemo(
    () => ({
      view,
      page,
      academic_year_id: yearId,
      term_id: termId,
    }),
    [view, page, yearId, termId],
  );

  const { data, isLoading, isError, error, refetch } = useAcademicCalendarConfigurationPage(queryParams);
  const publishCal = usePublishAcademicCalendarConfiguration();

  useEffect(() => {
    if (data?.selected_academic_year_id) setYearId(data.selected_academic_year_id);
    if (data?.selected_term_id) setTermId(data.selected_term_id ?? undefined);
    if (data?.active_view) setView(data.active_view);
  }, [data?.selected_academic_year_id, data?.selected_term_id, data?.active_view]);

  const syncUrl = (nextView: string, nextPage: number) => {
    const params = new URLSearchParams();
    if (nextView !== "list") params.set("view", nextView);
    if (nextPage > 1) params.set("page", String(nextPage));
    const q = params.toString();
    router.replace(q ? `?${q}` : "?", { scroll: false });
  };

  const pickView = (key: string) => {
    setView(key);
    setPage(1);
    syncUrl(key, 1);
  };

  const handlePublish = () => {
    if (!data?.selected_academic_year_id) return;
    publishCal.mutate({
      academic_year_id: data.selected_academic_year_id,
      calendar_id: data.primary_calendar_id,
    });
  };

  const selectedYear = yearId ?? data?.selected_academic_year_id;
  const addEventHref = selectedYear
    ? `/college-admin/academics/create-calendar-event?academic_year_id=${encodeURIComponent(selectedYear)}`
    : "/college-admin/academics/create-calendar-event";

  return (
    <div className="space-y-5" data-figma-frame="69:142093">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Academic Calendar Configuration"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">{data?.page_subtitle}</p>
        </div>
        <div className="flex shrink-0 flex-wrap items-center gap-2">
          <CollegeAdminSecondaryButton
            disabled={!data?.can_publish || publishCal.isPending}
            onClick={handlePublish}
          >
            <SendIcon className="size-3.5" aria-hidden />
            {data?.publish_button_label ?? "Publish calendar"}
          </CollegeAdminSecondaryButton>
          <CollegeAdminPrimaryLink href={addEventHref}>
            <CollegeAdminPlusActionLabel iconClassName="size-3.5" label={data?.add_event_button_label ?? "Add event" } />
          </CollegeAdminPrimaryLink>
        </div>
      </div>

      {data?.sub_nav?.length ? <YearsSemestersSubNav items={data.sub_nav} /> : null}

      {data?.view_tabs?.length ? (
        <CollegeAdminSectionNav
          items={data.view_tabs.map((tab) => ({
            key: tab.key,
            label: tab.label,
            active: tab.active || view === tab.key,
          }))}
          onSelect={(key) => pickView(key)}
        />
      ) : null}

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <div className="grid gap-5 lg:grid-cols-3">
            <CollegeAdminTablePanel
              className="lg:col-span-2"
              title={data.list_panel_title}
              footer={
                <>
                  <span>{data.year_event_count_label}</span>
                  {data.pagination.total_pages > 0 ? (
                    <CalendarPagination data={data} page={page} setPage={setPage} syncUrl={syncUrl} view={view} />
                  ) : null}
                </>
              }
            >
              {data.event_rows.length ? (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[40rem] text-left text-[13px]">
                    <thead>
                      <tr className="border-b border-[#f1f5f9] text-[11px] font-semibold uppercase tracking-wide text-[#94a3b8]">
                        {data.table_headers.map((header, index) => (
                          <th
                            key={header}
                            className={cn(
                              "pb-3 pt-4 font-medium",
                              index === 0 ? "px-5" : "pr-3",
                              index === data.table_headers.length - 1 ? "pr-5" : "",
                            )}
                          >
                            {header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#f1f5f9]">
                      {data.event_rows.map((row) => (
                        <tr key={row.event_id} className="transition-colors hover:bg-[#f8fafc]">
                          <td className="px-5 py-3.5 font-medium text-[#111827]">{row.title}</td>
                          <td className="py-3.5 pr-3 tabular-nums text-[#374151]">{row.date_label}</td>
                          <td className="py-3.5 pr-3 text-[#374151]">{row.type_label}</td>
                          <td className="py-3.5 pr-3 text-[#374151]">{row.audience_label}</td>
                          <td className="py-3.5 pr-5">
                            <StatusPill label={row.status_label} tone={row.status_tone} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <CollegeAdminPanelEmptyState
                  iconSlug="calendar-days"
                  title="No events in this view"
                  description="Add an event or configure semester milestones so students and staff see the right dates on the academic calendar."
                  action={
                    <CollegeAdminPrimaryLink href={addEventHref}>
                      <CollegeAdminPlusActionLabel iconClassName="size-3.5" label={data.add_event_button_label } />
                    </CollegeAdminPrimaryLink>
                  }
                />
              )}
            </CollegeAdminTablePanel>

            <CalendarTypeStatsSidebar data={data} addEventHref={addEventHref} addEventLabel={data.add_event_button_label} />
          </div>
        ) : null}
      </QueryState>
    </div>
  );
}

function CalendarPagination({
  data,
  page,
  setPage,
  syncUrl,
  view,
}: {
  data: AcademicCalendarConfigurationPage;
  page: number;
  setPage: (n: number) => void;
  syncUrl: (view: string, page: number) => void;
  view: string;
}) {
  return (
    <div className="flex items-center gap-1">
      <button
        type="button"
        className="rounded border border-[#dce3ec] px-2 py-1 disabled:opacity-40"
        disabled={!data.pagination.has_previous}
        onClick={() => {
          const next = Math.max(1, page - 1);
          setPage(next);
          syncUrl(view, next);
        }}
      >
        ‹
      </button>
      {data.pagination.page_numbers.map((num, index) =>
        num === -1 ? (
          <span key={`e-${index}`} className="px-1">
            …
          </span>
        ) : (
          <button
            key={num}
            type="button"
            className={cn(
              "min-w-8 rounded border px-2 py-1 tabular-nums",
              num === data.pagination.page ? "border-[#245dd8] bg-[#eff6ff] text-[#245dd8]" : "border-[#dce3ec]",
            )}
            onClick={() => {
              setPage(num);
              syncUrl(view, num);
            }}
          >
            {num}
          </button>
        ),
      )}
      <button
        type="button"
        className="rounded border border-[#dce3ec] px-2 py-1 disabled:opacity-40"
        disabled={!data.pagination.has_next}
        onClick={() => {
          const next = page + 1;
          setPage(next);
          syncUrl(view, next);
        }}
      >
        ›
      </button>
    </div>
  );
}

function CalendarTypeStatsSidebar({
  data,
  addEventHref,
  addEventLabel,
}: {
  data: AcademicCalendarConfigurationPage;
  addEventHref: string;
  addEventLabel: string;
}) {
  return (
    <div className="flex flex-col gap-5 max-lg:contents lg:col-span-1">
      <CollegeAdminSidePanel
        title="Quick actions"
        description="Use the guided wizard — same flow as semester and academic year setup."
      >
        <CollegeAdminPrimaryLink href={addEventHref} className="w-full justify-center">
          <CollegeAdminPlusActionLabel iconClassName="size-3.5" label={addEventLabel } />
        </CollegeAdminPrimaryLink>
      </CollegeAdminSidePanel>

      <CollegeAdminSidePanel title={data.type_stats_title}>
        {data.type_stats.length ? (
          <div className="space-y-4">
            {data.type_stats.map((row) => (
              <div key={row.type_label}>
                <div className="mb-1.5 flex items-center justify-between text-[12px]">
                  <span className="font-medium text-[#374151]">{row.type_label}</span>
                  <span className="tabular-nums text-[#64748b]">{row.count}</span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-[#e8ecf2]">
                  <div className="h-full rounded-full bg-[#245dd8]" style={{ width: `${row.bar_percent}%` }} />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-[13px] leading-relaxed text-[#94a3b8]">No events recorded for this academic year yet.</p>
        )}
      </CollegeAdminSidePanel>
    </div>
  );
}