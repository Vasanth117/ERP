"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";

import { CalendarIcon } from "@/components/icons/erp/generated/calendar";
import { FilterIcon } from "@/components/icons/erp/generated/filter";
import { Button } from "@/components/ui/button";
import {
  CollegeAdminChevronDown,
  CollegeAdminDownload,
} from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { fetchAcademicYears, fetchProgrammes } from "@/features/college-admin/api/academics";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useFinanceOverview } from "@/features/college-admin/hooks/use-finance-overview";
import { cn } from "@/lib/utils";


function formatInrCompact(amount: number) {
  if (amount >= 10_000_000) {
    const cr = amount / 10_000_000;
    return `₹${cr % 1 === 0 ? cr.toFixed(1) : cr.toFixed(1)} Cr`;
  }
  if (amount >= 100_000) {
    return `₹${(amount / 100_000).toFixed(1)} L`;
  }
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(amount);
}

function formatInrTable(amount: number) {
  if (amount >= 10_000_000) {
    return `₹${(amount / 10_000_000).toFixed(1)} Cr`;
  }
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: amount < 100_000 ? 0 : 1,
    notation: amount >= 100_000 ? "compact" : "standard",
  }).format(amount);
}

function StatusPill({ statusKey, label }: { statusKey: string; label: string }) {
  const tone =
    statusKey === "healthy"
      ? "bg-[#ecfdf5] text-[#047857]"
      : statusKey === "at_risk"
        ? "bg-[#fef2f2] text-[#b91c1c]"
        : "bg-[#fff7ed] text-[#c2410c]";
  const dot =
    statusKey === "healthy" ? "bg-[#10b981]" : statusKey === "at_risk" ? "bg-[#ef4444]" : "bg-[#f97316]";
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-medium", tone)}>
      <span className={cn("size-1.5 rounded-full", dot)} />
      {label}
    </span>
  );
}

function Panel({
  title,
  children,
  actionHref,
  actionLabel,
}: {
  title: string;
  children: ReactNode;
  actionHref?: string;
  actionLabel?: string;
}) {
  return (
    <section className="rounded-xl border border-[#e8ecf2] bg-white p-4 shadow-[0_1px_2px_rgba(15,23,42,0.04)] sm:p-5">
      <div className="mb-4 flex items-center justify-between gap-2">
        <h3 className="text-[14px] font-semibold text-[#111827]">{title}</h3>
        {actionHref && actionLabel ? (
          <Link href={actionHref} className="text-[12px] font-medium text-[#245dd8] hover:underline">
            {actionLabel}
          </Link>
        ) : null}
      </div>
      {children}
    </section>
  );
}

function KpiCard({
  label,
  value,
  hint,
  hintTone,
}: {
  label: string;
  value: string | number;
  hint?: ReactNode;
  hintTone?: "success" | "warning" | "muted";
}) {
  const toneClass =
    hintTone === "success" ? "text-[#059669]" : hintTone === "warning" ? "text-[#d97706]" : "text-[#9ca3af]";
  return (
    <div className="flex min-h-[7.25rem] flex-col rounded-xl border border-[#e8ecf2] bg-white p-5">
      <p className="text-[12px] font-medium text-[#6b7280]">{label}</p>
      <p className="mt-3 text-[1.75rem] font-bold tabular-nums text-[#111827]">{value}</p>
      {hint ? <p className={cn("mt-auto pt-3 text-[12px]", toneClass)}>{hint}</p> : <span className="mt-auto block min-h-[1.125rem]" aria-hidden />}
    </div>
  );
}

function MonthlyCollectionChart({
  points,
}: {
  points: { label: string; amount: number; isMtd: boolean }[];
}) {
  if (!points.length) {
    return <p className="text-sm text-[#9ca3af]">No verified payments recorded for this academic year yet.</p>;
  }
  const max = Math.max(...points.map((p) => p.amount), 1);
  return (
    <div className="flex h-44 items-end justify-between gap-2">
      {points.map((p) => (
        <div key={p.label} className="flex flex-1 flex-col items-center gap-1">
          <span className="text-[10px] tabular-nums text-[#6b7280]">{formatInrCompact(p.amount)}</span>
          <div
            className={cn("w-full max-w-[52px] rounded-t-md", p.isMtd ? "bg-[#93c5fd]" : "bg-[#245dd8]")}
            style={{ height: `${Math.max(8, (p.amount / max) * 100)}%` }}
          />
          <span className="max-w-[3rem] text-center text-[9px] leading-tight text-[#9ca3af]">{p.label}</span>
        </div>
      ))}
    </div>
  );
}

function ModeBars({ items }: { items: { label: string; share: number | null }[] }) {
  if (!items.length) return <p className="text-sm text-[#9ca3af]">No payment data.</p>;
  return (
    <ul className="space-y-3">
      {items.map((item) => (
        <li key={item.label}>
          <div className="mb-1 flex justify-between text-[12px]">
            <span className="text-[#374151]">{item.label}</span>
            <span className="tabular-nums text-[#6b7280]">{item.share != null ? `${item.share}%` : "—"}</span>
          </div>
          <div className="h-2 rounded-full bg-[#eef2f7]">
            <div
              className="h-full rounded-full bg-[#245dd8]"
              style={{ width: `${item.share != null ? Math.max(4, item.share) : 4}%` }}
            />
          </div>
        </li>
      ))}
    </ul>
  );
}

function AttentionBadge({ itemKey, count }: { itemKey: string; count: number }) {
  const tone =
    itemKey === "failed_payments"
      ? "bg-[#fef2f2] text-[#b91c1c]"
      : itemKey === "unreconciled"
        ? "bg-[#fff7ed] text-[#c2410c]"
        : "bg-[#eff6ff] text-[#1d4ed8]";
  return (
    <span className={cn("rounded-full px-2.5 py-0.5 text-[12px] font-semibold tabular-nums", tone)}>{count}</span>
  );
}

function FilterSelect({
  value,
  onChange,
  active,
  children,
  disabled,
  "aria-label": ariaLabel,
  className,
  leadingIcon,
}: {
  value: string;
  onChange: (v: string) => void;
  active?: boolean;
  children: ReactNode;
  disabled?: boolean;
  "aria-label"?: string;
  className?: string;
  leadingIcon?: ReactNode;
}) {
  return (
    <div className={cn("relative inline-flex min-w-[8.75rem]", className)}>
      {leadingIcon ? (
        <span
          className={cn(
            "pointer-events-none absolute left-2.5 top-1/2 z-[1] -translate-y-1/2",
            active ? "text-[#245dd8]" : "text-[#6b7280]",
          )}
          aria-hidden
        >
          {leadingIcon}
        </span>
      ) : null}
      <select
        aria-label={ariaLabel}
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
        className={cn(
          "w-full appearance-none truncate rounded-md border py-1.5 pr-8 text-xs",
          leadingIcon ? "pl-8" : "pl-3",
          active ? "border-[#245dd8] bg-[#eef4ff] font-medium text-[#245dd8]" : "border-[#e5e7eb] bg-white text-[#374151]",
          disabled && "opacity-60",
        )}
      >
        {children}
      </select>
      <CollegeAdminChevronDown className="pointer-events-none absolute right-2 top-1/2 size-3.5 -translate-y-1/2 text-[#6b7280]" />
    </div>
  );
}

export function FinanceSummaryDashboard() {
  const [academicYear, setAcademicYear] = useState("");
  const [programmeCode, setProgrammeCode] = useState("");
  const [feeHead, setFeeHead] = useState("");

  const yearsQ = useQuery({ queryKey: ["ca", "years", "finance"], queryFn: fetchAcademicYears });
  const programmesQ = useQuery({ queryKey: ["ca", "programmes", "finance"], queryFn: fetchProgrammes });

  const queryParams = useMemo(
    () => ({
      ...(academicYear ? { academic_year_label: academicYear } : {}),
      ...(programmeCode ? { programme_code: programmeCode } : {}),
      ...(feeHead ? { fee_head: feeHead } : {}),
    }),
    [academicYear, programmeCode, feeHead],
  );

  const { data, isLoading, isError, error, refetch, isFetching } = useFinanceOverview(queryParams);

  const defaultYear = useMemo(
    () => yearsQ.data?.find((y) => y.is_current)?.label ?? data?.filters.academic_year_label ?? "",
    [yearsQ.data, data],
  );

  useEffect(() => {
    if (!academicYear && defaultYear) setAcademicYear(defaultYear);
  }, [academicYear, defaultYear]);

  const yearDisplay = data?.academic_year_display ?? academicYear ?? defaultYear;

  const handleExport = useCallback(() => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `finance-summary-${new Date(data.generated_at).toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data]);

  const kpis = data?.kpis;
  const chartPoints = useMemo(
    () =>
      (data?.monthly_collection ?? []).map((p) => ({
        label: p.label,
        amount: p.amount_inr,
        isMtd: p.is_month_to_date,
      })),
    [data?.monthly_collection],
  );

  const modeItems = useMemo(
    () =>
      (data?.payment_modes ?? []).map((m) => ({
        label: m.label,
        share: m.share_pct,
      })),
    [data?.payment_modes],
  );

  return (
    <div className="space-y-5" data-figma-frame="66:3440">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold text-[#111827]">Finance summary</h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">
            Fee demand, collections, dues and concessions for {yearDisplay}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button type="button" className="h-9 gap-1.5 bg-[#245dd8] text-xs text-white" onClick={handleExport} disabled={!data}>
            <CollegeAdminDownload className="size-3.5" />
            Export statement
          </Button>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <FilterSelect
          value={academicYear || defaultYear || "__ph__"}
          onChange={setAcademicYear}
          active={Boolean(academicYear || defaultYear)}
          aria-label="Academic year"
          className="min-w-[9rem]"
          leadingIcon={<CalendarIcon className="size-3.5" />}
          disabled={yearsQ.isLoading}
        >
          {!academicYear && !defaultYear ? <option value="__ph__">Academic year</option> : null}
          {(yearsQ.data ?? []).map((y) => (
            <option key={y.label} value={y.label}>
              {y.label}
            </option>
          ))}
        </FilterSelect>
        <FilterSelect
          value={programmeCode}
          onChange={setProgrammeCode}
          active={Boolean(programmeCode)}
          aria-label="Programme"
          className="min-w-[11rem]"
          leadingIcon={<FilterIcon className="size-3.5" />}
          disabled={programmesQ.isLoading}
        >
          <option value="">All programmes</option>
          {(programmesQ.data ?? []).map((p) => (
            <option key={p.programme_id} value={p.code ?? p.name}>
              {p.name}
            </option>
          ))}
        </FilterSelect>
        <FilterSelect
          value={feeHead}
          onChange={setFeeHead}
          active={Boolean(feeHead)}
          aria-label="Fee head"
          className="min-w-[10rem]"
          leadingIcon={<FilterIcon className="size-3.5" />}
        >
          <option value="">All fee heads</option>
          {(data?.fee_head_options ?? []).map((h) => (
            <option key={h} value={h}>
              {h}
            </option>
          ))}
        </FilterSelect>
      </div>

      <QueryState isLoading={isLoading || isFetching} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
              <KpiCard
                label="Total fee demand"
                value={formatInrCompact(kpis?.total_demand_inr ?? 0)}
                hint={`${(kpis?.student_count ?? 0).toLocaleString("en-IN")} students · ${kpis?.fee_head_count ?? 0} fee heads`}
              />
              <KpiCard
                label="Collected"
                value={formatInrCompact(kpis?.collected_inr ?? 0)}
                hint={kpis?.collected_pct != null ? `${kpis.collected_pct}% of demand` : "No collections recorded"}
                hintTone="success"
              />
              <KpiCard
                label="Outstanding"
                value={formatInrCompact(kpis?.outstanding_inr ?? 0)}
                hint={`${(kpis?.students_with_dues ?? 0).toLocaleString("en-IN")} students with dues`}
                hintTone="warning"
              />
              <KpiCard
                label="Scholarships & concessions"
                value={formatInrCompact(kpis?.scholarships_concessions_inr ?? 0)}
                hint={`${(kpis?.scholarship_beneficiaries ?? 0).toLocaleString("en-IN")} beneficiaries`}
              />
            </div>

            <div className="grid gap-4 xl:grid-cols-3">
              <div className="space-y-4 xl:col-span-2">
                <Panel
                  title="Monthly collection"
                  actionHref="/college-admin/finance-administration"
                  actionLabel="Payment transactions →"
                >
                  <MonthlyCollectionChart points={chartPoints} />
                </Panel>
                <Panel
                  title="Outstanding dues by programme"
                  actionHref="/college-admin/finance-administration"
                  actionLabel="Outstanding dues →"
                >
                  {data.programme_dues_rows.length ? (
                    <>
                      <div className="overflow-x-auto">
                        <table className="w-full min-w-[44rem] text-left text-[12px]">
                          <thead>
                            <tr className="border-b border-[#e8ecf2] text-[#6b7280]">
                              <th className="pb-2 pr-2 font-medium">Programme</th>
                              <th className="pb-2 px-2 text-right font-medium">Demand</th>
                              <th className="pb-2 px-2 text-right font-medium">Collected</th>
                              <th className="pb-2 px-2 text-right font-medium">Outstanding</th>
                              <th className="pb-2 px-2 text-right font-medium">Students due</th>
                              <th className="pb-2 pl-2 font-medium">Status</th>
                            </tr>
                          </thead>
                          <tbody>
                            {data.programme_dues_rows.map((row) => (
                              <tr key={row.bucket_key} className="border-b border-[#f1f5f9]">
                                <td className="py-2 pr-2 font-medium text-[#111827]">{row.label}</td>
                                <td className="px-2 py-2 text-right tabular-nums">{formatInrTable(row.demand_amount)}</td>
                                <td className="px-2 py-2 text-right tabular-nums">{formatInrTable(row.collected_amount)}</td>
                                <td className="px-2 py-2 text-right tabular-nums">{formatInrTable(row.outstanding_amount)}</td>
                                <td className="px-2 py-2 text-right tabular-nums">{row.students_with_dues}</td>
                                <td className="py-2 pl-2">
                                  <StatusPill statusKey={row.status_key} label={row.status_label} />
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                      <div className="mt-3 flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] pt-3 text-[11px] text-[#6b7280]">
                        <span>Collection target: {data.collection_target_pct}%</span>
                        <Link href="/college-admin/finance-administration" className="font-medium text-[#245dd8] hover:underline">
                          Send reminders →
                        </Link>
                      </div>
                    </>
                  ) : (
                    <p className="text-sm text-[#9ca3af]">No programme-level fee data for the selected filters.</p>
                  )}
                </Panel>
              </div>
              <div className="space-y-4">
                <Panel
                  title="Collection by payment mode"
                  actionHref="/college-admin/finance-administration"
                  actionLabel="Reconciliation →"
                >
                  <ModeBars items={modeItems} />
                </Panel>
                <Panel
                  title="Needs attention"
                  actionHref="/college-admin/finance-administration"
                  actionLabel="Finance administration →"
                >
                  <ul className="divide-y divide-[#f1f5f9]">
                    {data.attention_items.map((item) => (
                      <li key={item.item_key} className="flex items-center justify-between gap-2 py-3 first:pt-0">
                        <p className="text-[13px] font-medium text-[#111827]">{item.label}</p>
                        <AttentionBadge itemKey={item.item_key} count={item.count} />
                      </li>
                    ))}
                  </ul>
                </Panel>
                <Panel
                  title="Scholarship disbursement"
                  actionHref="/college-admin/finance-administration"
                  actionLabel="Scholarships →"
                >
                  {data.scholarship_disbursements.length ? (
                    <ul className="divide-y divide-[#f1f5f9]">
                      {data.scholarship_disbursements.map((item) => (
                        <li key={item.program_label} className="flex items-center justify-between gap-2 py-3 first:pt-0">
                          <p className="text-[13px] text-[#374151]">{item.program_label}</p>
                          <span className="text-[12px] font-semibold tabular-nums text-[#111827]">
                            {formatInrCompact(item.amount_inr)}
                          </span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm text-[#9ca3af]">No scholarship or concession disbursements recorded yet.</p>
                  )}
                </Panel>
              </div>
            </div>

            <footer className="flex flex-wrap justify-between gap-2 border-t border-[#e8ecf2] pt-4 text-[11px] text-[#9ca3af]">
              <span>Live institutional data · Fees, payments and scholarships · All times IST</span>
            </footer>
          </>
        ) : null}
      </QueryState>
    </div>
  );
}