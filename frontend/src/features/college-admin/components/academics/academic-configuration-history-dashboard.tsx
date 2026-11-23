"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { CalendarDaysIcon } from "@/components/icons/erp/generated/calendar-days";
import { FilterIcon } from "@/components/icons/erp/generated/filter";
import { CollegeAdminDownload } from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { CollegeAdminSecondaryButton } from "@/features/college-admin/components/ui/college-admin-action-button";
import {
  CollegeAdminPanelEmptyState,
  CollegeAdminSidePanel,
  CollegeAdminTablePanel,
} from "@/features/college-admin/components/ui/dashboard-panel-ui";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useAcademicConfigurationHistoryPage } from "@/features/college-admin/hooks/use-academic-configuration-history";
import type { ConfigurationChangeRow } from "@/features/college-admin/types/institution";
import { cn } from "@/lib/utils";

function StatusPill({ label, tone }: { label: string; tone: string }) {
  const styles: Record<string, string> = {
    success: "bg-[#ecfdf5] text-[#047857]",
    warning: "bg-[#fff7ed] text-[#c2410c]",
    error: "bg-[#fef2f2] text-[#b91c1c]",
    muted: "bg-[#f3f4f6] text-[#6b7280]",
  };
  const dot: Record<string, string> = {
    success: "bg-[#10b981]",
    warning: "bg-[#f97316]",
    error: "bg-[#ef4444]",
    muted: "bg-[#9ca3af]",
  };
  const key = tone in styles ? tone : "muted";
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-medium", styles[key])}>
      <span className={cn("size-1.5 rounded-full", dot[key])} />
      {label}
    </span>
  );
}

function FilterSelect({
  icon,
  label,
  value,
  onChange,
  options,
}: {
  icon?: React.ReactNode;
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <div className="relative">
      {icon ? <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[#9ca3af]">{icon}</span> : null}
      <select
        aria-label={label}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={cn(
          "h-9 min-w-[9rem] rounded-md border border-[#dce3ec] bg-white pr-8 text-[13px] text-[#374151]",
          icon ? "pl-9" : "pl-3",
        )}
      >
        {options.map((opt) => (
          <option key={`${opt.value}-${opt.label}`} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
}

export function AcademicConfigurationHistoryDashboard() {
  const [page, setPage] = useState(1);
  const [dateRange, setDateRange] = useState("last_6_months");
  const [settingArea, setSettingArea] = useState("");
  const [actorId, setActorId] = useState("");
  const [selectedId, setSelectedId] = useState<string | undefined>();

  useEffect(() => {
    setPage(1);
  }, [dateRange, settingArea, actorId]);

  const { data, isLoading, isError, error, refetch } = useAcademicConfigurationHistoryPage({
    page,
    date_range: dateRange,
    setting_area: settingArea || undefined,
    actor_id: actorId || undefined,
    selected_change_id: selectedId,
  });

  useEffect(() => {
    if (data?.selected_change && !selectedId) {
      setSelectedId(data.selected_change.change_id);
    }
  }, [data?.selected_change, selectedId]);

  const handleExport = useCallback(() => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `academic-configuration-history-${new Date(data.generated_at).toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data]);

  const pickRow = (row: ConfigurationChangeRow) => {
    setSelectedId(row.change_id);
  };

  const headers = data?.table_headers ?? [];

  return (
    <div className="space-y-5" data-figma-frame="69:142605">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Academic Configuration History"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">{data?.page_subtitle}</p>
        </div>
      </div>

      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-wrap items-center gap-2">
          <FilterSelect
            icon={<CalendarDaysIcon className="size-4" aria-hidden />}
            label={data?.date_range_filter_label ?? "Date range"}
            value={dateRange}
            onChange={setDateRange}
            options={data?.date_range_options ?? [{ value: "last_6_months", label: "Last 6 months" }]}
          />
          <FilterSelect
            icon={<FilterIcon className="size-4" aria-hidden />}
            label={data?.setting_filter_label ?? "Area"}
            value={settingArea}
            onChange={setSettingArea}
            options={data?.setting_options ?? [{ value: "", label: "All areas" }]}
          />
          <FilterSelect
            icon={<FilterIcon className="size-4" aria-hidden />}
            label={data?.user_filter_label ?? "User"}
            value={actorId}
            onChange={setActorId}
            options={data?.user_options ?? [{ value: "", label: "All users" }]}
          />
        </div>
        <CollegeAdminSecondaryButton onClick={handleExport} disabled={!data} className="shrink-0">
          <CollegeAdminDownload className="size-3.5" />
          {data?.export_label ?? "Export log"}
        </CollegeAdminSecondaryButton>
      </div>

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_360px]">
              <CollegeAdminTablePanel
                title={data.change_log_title}
                footer={
                  <>
                    <span>{data.showing_label}</span>
                    {data.pagination.total_pages > 0 ? (
                      <HistoryPagination data={data} page={page} setPage={setPage} />
                    ) : null}
                  </>
                }
              >
                {data.changes.length ? (
                  <table className="w-full text-left text-[13px]">
                    <thead>
                      <tr className="border-b border-[#f1f5f9] text-[11px] font-semibold uppercase tracking-wide text-[#94a3b8]">
                        {headers.map((header, index) => (
                          <th
                            key={header}
                            className={cn("pb-3 pt-4 font-medium", index === 0 ? "px-5" : "pr-3", index === headers.length - 1 ? "pr-5" : "")}
                          >
                            {header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#f1f5f9]">
                      {data.changes.map((row) => (
                        <tr
                          key={row.change_id}
                          className={cn(
                            "cursor-pointer transition-colors hover:bg-[#f8fafc]",
                            data.selected_change?.change_id === row.change_id && "bg-[#eff6ff]",
                          )}
                          onClick={() => pickRow(row)}
                        >
                          <td className="px-5 py-3.5 font-medium text-[#111827]">{row.change_summary}</td>
                          <td className="py-3.5 pr-3 text-[#374151]">{row.setting_label}</td>
                          <td className="py-3.5 pr-3 text-[#374151]">{row.changed_by_label}</td>
                          <td className="py-3.5 pr-3 tabular-nums text-[#374151]">{row.when_label}</td>
                          <td className="py-3.5 pr-5">
                            <StatusPill label={row.status_label} tone={row.status_tone} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <CollegeAdminPanelEmptyState
                    iconSlug="history"
                    title="No changes in this view"
                    description="Adjust the date range, area, or user filters, or export the current log when entries are available."
                  />
                )}
              </CollegeAdminTablePanel>

              <div className="space-y-5">
                {data.selected_change ? (
                  <CollegeAdminSidePanel title={data.change_details_title}>
                    <div className="mb-3 flex justify-end">
                      <Link
                        href={data.selected_change.open_href}
                        className="text-[12px] font-semibold text-[#245dd8] hover:underline"
                      >
                        {data.selected_change.open_label} →
                      </Link>
                    </div>
                    <dl className="space-y-3 text-[13px]">
                      <div>
                        <dt className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">Change</dt>
                        <dd className="mt-0.5 font-medium text-[#111827]">{data.selected_change.setting_line}</dd>
                      </div>
                      {data.selected_change.reason_line ? (
                        <div>
                          <dt className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">Reason</dt>
                          <dd className="mt-0.5 text-[#374151]">{data.selected_change.reason_line}</dd>
                        </div>
                      ) : null}
                      {data.selected_change.approved_by_label ? (
                        <div>
                          <dt className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">Approved by</dt>
                          <dd className="mt-0.5 text-[#374151]">{data.selected_change.approved_by_label}</dd>
                        </div>
                      ) : null}
                      {data.selected_change.applies_to_line ? (
                        <div>
                          <dt className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">Applies to</dt>
                          <dd className="mt-0.5 text-[#374151]">{data.selected_change.applies_to_line}</dd>
                        </div>
                      ) : null}
                    </dl>
                  </CollegeAdminSidePanel>
                ) : null}

                <CollegeAdminSidePanel title={data.changes_by_area_title}>
                  {data.changes_by_area.length ? (
                    <ul className="space-y-4">
                      {data.changes_by_area.map((row) => (
                        <li key={row.area_key}>
                          <div className="mb-1.5 flex items-center justify-between text-[13px]">
                            <span className="text-[#374151]">{row.title}</span>
                            <span className="font-medium tabular-nums text-[#111827]">{row.count}</span>
                          </div>
                          <div className="h-2 overflow-hidden rounded-full bg-[#f1f5f9]">
                            <div className="h-full rounded-full bg-[#245dd8]" style={{ width: `${row.progress_percent}%` }} />
                          </div>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-[13px] text-[#94a3b8]">No changes in this period.</p>
                  )}
                </CollegeAdminSidePanel>
              </div>
            </div>

          </>
        ) : null}
      </QueryState>
    </div>
  );
}

function HistoryPagination({
  data,
  page,
  setPage,
}: {
  data: NonNullable<ReturnType<typeof useAcademicConfigurationHistoryPage>["data"]>;
  page: number;
  setPage: (n: number) => void;
}) {
  return (
    <div className="flex items-center gap-1">
      <button
        type="button"
        className="rounded border border-[#dce3ec] px-2 py-1 text-xs disabled:opacity-40"
        disabled={!data.pagination.has_previous}
        onClick={() => setPage(Math.max(1, page - 1))}
      >
        ‹
      </button>
      {data.pagination.page_numbers.map((num, index) =>
        num === -1 ? (
          <span key={`ellipsis-${index}`} className="px-1">
            …
          </span>
        ) : (
          <button
            key={num}
            type="button"
            className={cn(
              "min-w-8 rounded border px-2 py-1 tabular-nums text-xs font-semibold",
              num === data.pagination.page ? "border-[#245dd8] bg-[#eff6ff] text-[#245dd8]" : "border-[#dce3ec]",
            )}
            onClick={() => setPage(num)}
          >
            {num}
          </button>
        ),
      )}
      <button
        type="button"
        className="rounded border border-[#dce3ec] px-2 py-1 text-xs disabled:opacity-40"
        disabled={!data.pagination.has_next}
        onClick={() => setPage(page + 1)}
      >
        ›
      </button>
    </div>
  );
}