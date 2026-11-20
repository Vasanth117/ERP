"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { CalendarDaysIcon } from "@/components/icons/erp/generated/calendar-days";
import { FilterIcon } from "@/components/icons/erp/generated/filter";
import { CollegeAdminDownload } from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useDepartmentStatusHistoryPage } from "@/features/college-admin/hooks/use-department-status-history";
import { cn } from "@/lib/utils";

function StatusPill({ label, tone }: { label: string; tone: string }) {
  const styles: Record<string, string> = {
    success: "bg-[#ecfdf5] text-[#047857]",
    warning: "bg-[#fff7ed] text-[#c2410c]",
    error: "bg-[#fef2f2] text-[#b91c1c]",
    muted: "bg-[#f3f4f6] text-[#6b7280]",
    info: "bg-[#eff6ff] text-[#1d4ed8]",
    purple: "bg-[#f5f3ff] text-[#6d28d9]",
  };
  const dot: Record<string, string> = {
    success: "bg-[#10b981]",
    warning: "bg-[#f97316]",
    error: "bg-[#ef4444]",
    muted: "bg-[#9ca3af]",
    info: "bg-[#3b82f6]",
    purple: "bg-[#8b5cf6]",
  };
  const key = tone in styles ? tone : "muted";
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-medium", styles[key])}>
      <span className={cn("size-1.5 rounded-full", dot[key])} />
      {label}
    </span>
  );
}

function SummaryBadge({ count, tone }: { count: number; tone: string }) {
  const styles: Record<string, string> = {
    success: "bg-[#ecfdf5] text-[#047857]",
    info: "bg-[#eff6ff] text-[#1d4ed8]",
    muted: "bg-[#ede9fe] text-[#5b21b6]",
  };
  const key = tone in styles ? tone : "muted";
  return (
    <span className={cn("rounded-full px-2 py-0.5 text-[11px] font-semibold tabular-nums", styles[key])}>{count}</span>
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
  const select = (
    <select
      aria-label={label}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className={cn(
        "h-9 min-w-[9rem] rounded-md border border-[#dce3ec] bg-white text-[13px] text-[#374151]",
        icon ? "pl-9 pr-3" : "px-3",
      )}
    >
      {options.map((opt) => (
        <option key={`${opt.value}-${opt.label}`} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  );
  if (!icon) return select;
  return (
    <div className="relative">
      <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[#9ca3af]">{icon}</span>
      {select}
    </div>
  );
}

function formatSnapshot(iso: string) {
  try {
    return new Intl.DateTimeFormat("en-IN", {
      dateStyle: "medium",
      timeStyle: "short",
      timeZone: "Asia/Kolkata",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

const TIMELINE_DOT: Record<string, string> = {
  success: "bg-[#10b981]",
  warning: "bg-[#f97316]",
  error: "bg-[#ef4444]",
  info: "bg-[#3b82f6]",
  muted: "bg-[#9ca3af]",
};

export function DepartmentStatusHistoryDashboard() {
  const [page, setPage] = useState(1);
  const [sinceYear, setSinceYear] = useState("2020");
  const [departmentId, setDepartmentId] = useState("");
  const [changeType, setChangeType] = useState("");
  const [selectedDepartmentId, setSelectedDepartmentId] = useState("");

  useEffect(() => {
    setPage(1);
  }, [sinceYear, departmentId, changeType]);

  const queryParams = useMemo(
    () => ({
      page,
      since_year: sinceYear || undefined,
      department_id: departmentId || undefined,
      change_type_filter: changeType || undefined,
      selected_department_id: selectedDepartmentId || departmentId || undefined,
    }),
    [page, sinceYear, departmentId, changeType, selectedDepartmentId],
  );

  const { data, isLoading, isError, error, refetch, isFetching } = useDepartmentStatusHistoryPage(queryParams);

  useEffect(() => {
    if (!data?.selected_timeline_department_id) return;
    if (!selectedDepartmentId) {
      setSelectedDepartmentId(data.selected_timeline_department_id);
    }
  }, [data?.selected_timeline_department_id, selectedDepartmentId]);

  const handleExport = useCallback(() => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `department-status-history-${new Date(data.generated_at).toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data]);

  const headers = data?.table_headers ?? [];

  return (
    <div className="space-y-5" data-figma-frame="69:135016">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Department Status & History"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">{data?.page_subtitle}</p>
        </div>
        <button
          type="button"
          className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8] disabled:opacity-50"
          onClick={handleExport}
          disabled={isLoading || !data}
        >
          <CollegeAdminDownload className="size-3.5" aria-hidden />
          {data?.export_label ?? "Export log"}
        </button>
      </div>

      {data ? (
        <div className="flex flex-col gap-3 lg:flex-row lg:flex-wrap lg:items-center lg:justify-between">
          <div className="flex flex-wrap items-center gap-2">
            <FilterSelect
              icon={<CalendarDaysIcon className="size-3.5" aria-hidden />}
              label={data.since_year_filter_label}
              value={sinceYear}
              onChange={setSinceYear}
              options={data.since_year_options}
            />
            <FilterSelect
              icon={<FilterIcon className="size-3.5" aria-hidden />}
              label={data.department_filter_label}
              value={departmentId}
              onChange={setDepartmentId}
              options={data.department_options}
            />
            <FilterSelect
              icon={<FilterIcon className="size-3.5" aria-hidden />}
              label={data.change_type_filter_label}
              value={changeType}
              onChange={setChangeType}
              options={data.change_type_options}
            />
            <span className="ml-2 inline-flex items-center gap-1.5 text-[12px] text-[#6b7280]">
              <span className="size-1.5 rounded-full bg-[#3b82f6]" />
              {data.scope_indicator_label}
            </span>
          </div>
          <span className="text-[12px] tabular-nums text-[#9ca3af]">
            <span className="mr-1 text-[#10b981]">●</span>
            {data.updated_at_label}
          </span>
        </div>
      ) : null}

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()} isEmpty={false}>
        {data ? (
          <div className={cn("grid gap-5 xl:grid-cols-[minmax(0,1fr)_18rem]", isFetching && "opacity-70")}>
            <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              {data.events.length ? (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[44rem] text-left text-[13px]">
                    <thead>
                      <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                        {headers.map((h, i) => (
                          <th
                            key={h}
                            className={cn("pb-3 pt-4 font-medium", i === 0 ? "px-5" : "pr-3", i === headers.length - 1 ? "pr-5" : "")}
                          >
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#f1f5f9]">
                      {data.events.map((row) => (
                        <tr
                          key={row.event_id}
                          className={cn(
                            "cursor-pointer hover:bg-[#f9fafb]",
                            data.selected_timeline_department_id === row.department_id && "bg-[#eff6ff]",
                          )}
                          onClick={() => setSelectedDepartmentId(row.department_id)}
                        >
                          <td className="px-5 py-3 font-medium text-[#111827]">{row.event_label}</td>
                          <td className="py-3 pr-3 text-[#374151]">{row.department_label}</td>
                          <td className="py-3 pr-3 text-[#374151]">{row.by_label}</td>
                          <td className="py-3 pr-3 tabular-nums text-[#374151]">{row.date_label}</td>
                          <td className="py-3 pr-5">
                            <StatusPill label={row.status_label} tone={row.status_tone} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="px-5 py-8 text-sm text-[#9ca3af]">No department events match your filters.</p>
              )}
              <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
                <span>{data.showing_label}</span>
                {data.pagination.total_pages > 0 ? (
                  <div className="flex items-center gap-1">
                    <button
                      type="button"
                      className="rounded border border-[#dce3ec] px-2 py-1 text-[12px] disabled:opacity-40"
                      disabled={!data.pagination.has_previous}
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
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
                            "min-w-8 rounded border px-2 py-1 tabular-nums",
                            num === data.pagination.page
                              ? "border-[#245dd8] bg-[#eff6ff] text-[#245dd8]"
                              : "border-[#dce3ec]",
                          )}
                          onClick={() => setPage(num)}
                        >
                          {num}
                        </button>
                      ),
                    )}
                    <button
                      type="button"
                      className="rounded border border-[#dce3ec] px-2 py-1 disabled:opacity-40"
                      disabled={!data.pagination.has_next}
                      onClick={() => setPage((p) => p + 1)}
                    >
                      ›
                    </button>
                  </div>
                ) : null}
              </div>
            </section>

            <aside className="space-y-4">
              <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.status_summary_title}</h3>
                <ul className="mt-4 space-y-4">
                  {data.status_summary_items.map((item) => (
                    <li key={item.key} className="flex items-start justify-between gap-2">
                      <div>
                        <p className="text-[13px] font-semibold text-[#111827]">{item.title}</p>
                        <p className="mt-0.5 text-[12px] text-[#6b7280]">{item.subtitle}</p>
                      </div>
                      <SummaryBadge count={item.count} tone={item.badge_tone} />
                    </li>
                  ))}
                </ul>
              </section>

              <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.timeline_section_title}</h3>
                <ul className="mt-4 space-y-0 border-l border-[#e5e7eb] pl-4">
                  {data.timeline_items.length ? (
                    data.timeline_items.map((item, index) => (
                      <li key={item.event_id} className={cn("relative pb-5", index === data.timeline_items.length - 1 && "pb-0")}>
                        <span
                          className={cn(
                            "absolute -left-[1.3125rem] top-1 size-2.5 rounded-full border-2 border-white ring-1 ring-[#e5e7eb]",
                            TIMELINE_DOT[item.tone] ?? TIMELINE_DOT.info,
                          )}
                        />
                        <p className="text-[13px] font-medium text-[#111827]">{item.title}</p>
                        <p className="mt-0.5 text-[12px] tabular-nums text-[#9ca3af]">{item.date_label}</p>
                        {item.nested_status_label ? (
                          <div className="mt-1.5">
                            <StatusPill label={item.nested_status_label} tone="warning" />
                          </div>
                        ) : null}
                      </li>
                    ))
                  ) : (
                    <li className="text-[13px] text-[#9ca3af]">No timeline for this department.</li>
                  )}
                </ul>
              </section>
            </aside>
          </div>
        ) : null}
      </QueryState>

      {data ? (
        <footer className="flex flex-col gap-2 border-t border-[#e8ecf2] pt-4 text-[11px] text-[#9ca3af] sm:flex-row sm:items-center sm:justify-between">
          <p>{data.footer_disclaimer}</p>
          <p className="tabular-nums">
            {data.footer_snapshot_label} · {formatSnapshot(data.generated_at)}
          </p>
        </footer>
      ) : null}
    </div>
  );
}