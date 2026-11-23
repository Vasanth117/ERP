"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { CalendarIcon } from "@/components/icons/erp/generated/calendar";
import { FilterIcon } from "@/components/icons/erp/generated/filter";
import { Button } from "@/components/ui/button";
import {
  CollegeAdminChevronRight,
  CollegeAdminDownload,
} from "@/features/college-admin/components/layout/college-admin-erp-icons";
import {
  CollegeAdminKpiGrid,
  CollegeAdminUserDashboardKpiCard,
} from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useFinanceDashboardPage } from "@/features/college-admin/hooks/use-finance-dashboard";
import type { FinanceProgrammeCollectionItem } from "@/features/college-admin/types/finance-dashboard";
import { cn } from "@/lib/utils";

function formatAyLabel(label: string) {
  const match = label.match(/^(\d{4})-(\d{2,4})$/);
  if (match) {
    const end = match[2].length === 2 ? match[1].slice(0, 2) + match[2] : match[2];
    return `AY ${match[1]}–${end}`;
  }
  return label.startsWith("AY ") ? label : label ? `AY ${label}` : label;
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
      {icon ? (
        <span className="pointer-events-none absolute left-3 top-1/2 z-[1] -translate-y-1/2 text-[#9ca3af]">
          {icon}
        </span>
      ) : null}
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
            {opt.label.startsWith("AY ") || opt.value === "" ? opt.label : formatAyLabel(opt.label)}
          </option>
        ))}
      </select>
    </div>
  );
}

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

const BAR_COLORS: Record<string, string> = {
  green: "bg-[#10b981]",
  blue: "bg-[#245dd8]",
  amber: "bg-[#b45309]",
  teal: "bg-[#0d9488]",
  indigo: "bg-[#6366f1]",
};

function CollectionByProgramme({ items }: { items: FinanceProgrammeCollectionItem[] }) {
  if (!items.length) {
    return <p className="text-sm text-[#9ca3af]">No programme collection data for the selected filters.</p>;
  }
  return (
    <ul className="space-y-4">
      {items.map((item) => (
        <li key={item.key}>
          <div className="mb-1.5 flex justify-between gap-2 text-[13px]">
            <span className="font-medium text-[#111827]">{item.label}</span>
            <span className="shrink-0 tabular-nums text-[#374151]">{item.collection_percent}%</span>
          </div>
          <div className="h-2 rounded-full bg-[#eef2f7]">
            <div
              className={cn("h-full rounded-full", BAR_COLORS[item.bar_tone] ?? "bg-[#245dd8]")}
              style={{ width: `${Math.min(100, Math.max(4, item.collection_percent))}%` }}
            />
          </div>
        </li>
      ))}
    </ul>
  );
}

export function FinanceDashboard() {
  const [page, setPage] = useState(1);
  const [academicYear, setAcademicYear] = useState("");
  const [programme, setProgramme] = useState("");

  const queryParams = useMemo(
    () => ({
      page,
      academic_year_code: academicYear || undefined,
      programme_code: programme || undefined,
    }),
    [page, academicYear, programme],
  );

  const { data, isLoading, isError, error, refetch, isFetching } = useFinanceDashboardPage(queryParams);

  useEffect(() => {
    if (data?.selected_academic_year && !academicYear) {
      setAcademicYear(data.selected_academic_year);
    }
  }, [data?.selected_academic_year, academicYear]);

  useEffect(() => {
    setPage(1);
  }, [academicYear, programme]);

  const handleExport = useCallback(() => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `finance-dashboard-${new Date(data.generated_at).toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data]);

  return (
    <div className="space-y-5" data-figma-frame="160:2199">
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
              {data?.page_title ?? "Finance Dashboard"}
            </h2>
            <p className="mt-1 text-[14px] text-[#6b7280]">
              {data?.page_subtitle ?? "Fee collection and payment monitoring"}
            </p>
          </div>
          <div className="flex shrink-0 flex-wrap gap-2">
            <Button
              type="button"
              variant="outline"
              className="h-9 gap-1.5 border-[#dce3ec] text-xs font-medium text-[#374151]"
              onClick={handleExport}
              disabled={isLoading || !data}
            >
              <CollegeAdminDownload className="size-3.5" />
              {data?.export_label ?? "Export"}
            </Button>
            <Link
              href={data?.open_portal_href ?? "/college-admin/dashboard/finance-summary"}
              className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
            >
              {data?.open_portal_label ?? "Open Finance portal"}
              <CollegeAdminChevronRight className="size-3.5" aria-hidden />
            </Link>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <FilterSelect
            icon={<CalendarIcon className="size-3.5" aria-hidden />}
            label={data?.academic_year_filter_label ?? "Academic year"}
            value={academicYear}
            onChange={setAcademicYear}
            options={
              data?.academic_year_options?.map((o) => ({
                value: o.value,
                label: formatAyLabel(o.label),
              })) ?? []
            }
          />
          <FilterSelect
            icon={<FilterIcon className="size-3.5" aria-hidden />}
            label={data?.programme_filter_label ?? "Programme"}
            value={programme}
            onChange={setProgramme}
            options={data?.programme_options ?? [{ value: "", label: "All programmes" }]}
          />
          {isFetching && !isLoading ? (
            <span className="text-[12px] text-[#9ca3af]">Updating…</span>
          ) : null}
        </div>
      </div>

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            <CollegeAdminKpiGrid>
              {data.kpis.map((kpi, index) => (
                <CollegeAdminUserDashboardKpiCard key={kpi.key} kpi={kpi} index={index} />
              ))}
            </CollegeAdminKpiGrid>

            <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_320px]">
              <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <div className="flex items-center justify-between border-b border-[#f1f5f9] px-5 py-3.5">
                  <h3 className="text-[14px] font-semibold text-[#111827]">{data.transactions_section_title}</h3>
                  <Link
                    href="/college-admin/finance/payment-transactions"
                    className="text-[12px] font-medium text-[#245dd8] hover:underline"
                  >
                    {data.transactions_count_label}
                  </Link>
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
                                "pb-3 font-medium",
                                index === 0 ? "pl-5 pr-3" : "pr-3",
                                index === data.table_headers.length - 1 ? "pr-5" : "",
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
                            <td className="py-3 pr-5">
                              <StatusPill label={row.status_label} tone={row.status_tone} />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="px-5 py-10 text-center text-sm text-[#9ca3af]">No payment transactions yet.</p>
                )}
                <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
                  <span>{data.showing_label}</span>
                  {data.pagination.total_pages > 0 ? (
                    <div className="flex items-center gap-1">
                      <button
                        type="button"
                        className="rounded border border-[#dce3ec] px-2 py-1 disabled:opacity-40"
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

              <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <h3 className="mb-4 text-[14px] font-semibold text-[#111827]">{data.collection_section_title}</h3>
                <CollectionByProgramme items={data.programme_collection_items} />
              </section>
            </div>
          </>
        ) : null}
      </QueryState>
    </div>
  );
}