"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { CheckIcon } from "@/components/icons/erp/generated/check";
import { RefreshCwIcon } from "@/components/icons/erp/generated/refresh-cw";
import { Input } from "@/components/ui/input";
import { CreditGradingSubNav } from "@/features/college-admin/components/academics/credit-grading-sub-nav";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useCreditConfigurationPage,
  useResetCreditConfiguration,
  useSaveCreditConfiguration,
} from "@/features/college-admin/hooks/use-credit-grading";
import type { CreditLevelRow, RuleToggle } from "@/features/college-admin/types/credit-grading";
import { cn } from "@/lib/utils";

function RuleSwitch({ rule, checked, onChange }: { rule: RuleToggle; checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <div className="flex items-start justify-between gap-3 border-b border-[#f1f5f9] py-3.5 last:border-0">
      <div>
        <p className="text-[13px] font-medium text-[#111827]">{rule.title}</p>
        {rule.description ? <p className="text-[12px] text-[#6b7280]">{rule.description}</p> : null}
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={cn("relative h-6 w-11 shrink-0 rounded-full", checked ? "bg-[#245dd8]" : "bg-[#d1d5db]")}
      >
        <span className={cn("absolute top-0.5 size-5 rounded-full bg-white shadow transition-transform", checked ? "left-[22px]" : "left-0.5")} />
      </button>
    </div>
  );
}

function StatusPill({ label }: { label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-[#ecfdf5] px-2.5 py-0.5 text-[11px] font-medium text-[#047857]">
      <span className="size-1.5 rounded-full bg-[#10b981]" />
      {label}
    </span>
  );
}

export function CreditConfigurationDashboard() {
  const { data, isLoading, isError, error, refetch } = useCreditConfigurationPage();
  const save = useSaveCreditConfiguration();
  const reset = useResetCreditConfiguration();

  const [calc, setCalc] = useState<Record<string, string>>({});
  const [rules, setRules] = useState<Record<string, boolean>>({});
  const [levels, setLevels] = useState<CreditLevelRow[]>([]);

  useEffect(() => {
    if (!data) return;
    const c: Record<string, string> = {};
    for (const field of data.calculation_fields) c[field.key] = field.value;
    setCalc(c);
    const r: Record<string, boolean> = {};
    for (const rule of data.rules) r[rule.key] = rule.enabled;
    setRules(r);
    setLevels(data.level_rows.map((row) => ({ ...row })));
  }, [data]);

  const handleSave = () => {
    if (!data) return;
    save.mutate({ calculation: calc, rules, level_rows: levels });
  };

  const toneBadge = (tone: string, count: number) => {
    const cls =
      tone === "warning"
        ? "bg-[#fff7ed] text-[#c2410c]"
        : tone === "info"
          ? "bg-[#eff6ff] text-[#1d4ed8]"
          : "bg-[#f3f4f6] text-[#6b7280]";
    return <span className={cn("rounded-full px-2 py-0.5 text-[11px] font-semibold tabular-nums", cls)}>{count}</span>;
  };

  return (
    <div className="space-y-5" data-figma-frame="69:141424">
      {data?.sub_nav.length ? <CreditGradingSubNav items={data.sub_nav} /> : null}

      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold text-[#111827]">{data?.page_title ?? "Credit Configuration"}</h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">{data?.page_subtitle}</p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => reset.mutate()}
            disabled={reset.isPending}
            className="inline-flex h-9 items-center gap-1.5 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151]"
          >
            <RefreshCwIcon className="size-3.5" />
            {data?.reset_label ?? "Reset"}
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={save.isPending}
            className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white"
          >
            <CheckIcon className="size-3.5" />
            {data?.save_rules_label ?? "Save rules"}
          </button>
        </div>
      </div>

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <div className="grid gap-5 xl:grid-cols-3">
            <div className="space-y-5 xl:col-span-2">
              <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-sm">
                <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                  <h3 className="text-[14px] font-semibold text-[#111827]">{data.requirements_section_title}</h3>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[36rem] text-left text-[13px]">
                    <thead>
                      <tr className="text-[11px] uppercase tracking-wide text-[#9ca3af]">
                        {data.requirements_table_headers.map((h, i) => (
                          <th key={h} className={cn("pb-3 pt-4 font-medium", i === 0 ? "px-5" : "pr-3")}>
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#f1f5f9]">
                      {levels.map((row, index) => (
                        <tr key={row.level_key}>
                          <td className="px-5 py-3 font-medium text-[#111827]">{row.level_label}</td>
                          <td className="py-3 pr-3">
                            <Input
                              className="h-8 w-20 tabular-nums"
                              type="number"
                              value={row.min_graduate_credits}
                              onChange={(e) =>
                                setLevels((prev) => {
                                  const next = [...prev];
                                  next[index] = { ...row, min_graduate_credits: Number(e.target.value) };
                                  return next;
                                })
                              }
                            />
                          </td>
                          <td className="py-3 pr-3">
                            <Input
                              className="h-8 w-16 tabular-nums"
                              type="number"
                              value={row.max_per_semester}
                              onChange={(e) =>
                                setLevels((prev) => {
                                  const next = [...prev];
                                  next[index] = { ...row, max_per_semester: Number(e.target.value) };
                                  return next;
                                })
                              }
                            />
                          </td>
                          <td className="py-3 pr-3">
                            <Input
                              className="h-8 w-16 tabular-nums"
                              type="number"
                              value={row.min_per_semester}
                              onChange={(e) =>
                                setLevels((prev) => {
                                  const next = [...prev];
                                  next[index] = { ...row, min_per_semester: Number(e.target.value) };
                                  return next;
                                })
                              }
                            />
                          </td>
                          <td className="py-3 pr-5">
                            <StatusPill label={row.status_label} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="flex justify-between border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
                  <span>{data.requirements_footer_label}</span>
                  <Link href={data.requirements_edit_href} className="font-medium text-[#245dd8] hover:underline">
                    {data.requirements_edit_label}
                  </Link>
                </div>
              </section>

              <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-sm">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.calculation_section_title}</h3>
                <div className="mt-4 grid gap-4 sm:grid-cols-2">
                  {data.calculation_fields.map((field) => (
                    <div key={field.key} className={field.field_type === "select" ? "sm:col-span-2 sm:max-w-md" : undefined}>
                      <label className="text-[12px] text-[#6b7280]">{field.label}</label>
                      {field.field_type === "select" ? (
                        <select
                          className="mt-1 flex h-9 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px]"
                          value={calc[field.key] ?? ""}
                          onChange={(e) => setCalc((p) => ({ ...p, [field.key]: e.target.value }))}
                        >
                          {field.options.map((o) => (
                            <option key={o.value} value={o.value}>
                              {o.label}
                            </option>
                          ))}
                        </select>
                      ) : (
                        <Input
                          className="mt-1 h-9"
                          value={calc[field.key] ?? ""}
                          onChange={(e) => setCalc((p) => ({ ...p, [field.key]: e.target.value }))}
                        />
                      )}
                    </div>
                  ))}
                </div>
              </section>
            </div>

            <div className="space-y-4">
              <section className="rounded-xl border border-[#e8ecf2] bg-white px-5 py-2 shadow-sm">
                <h3 className="border-b border-[#f1f5f9] py-3.5 text-[14px] font-semibold text-[#111827]">{data.rules_section_title}</h3>
                {data.rules.map((rule) => (
                  <RuleSwitch
                    key={rule.key}
                    rule={rule}
                    checked={rules[rule.key] ?? rule.enabled}
                    onChange={(v) => setRules((p) => ({ ...p, [rule.key]: v }))}
                  />
                ))}
              </section>
              <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-sm">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.limits_section_title}</h3>
                <ul className="mt-4 space-y-4">
                  {data.limit_stats.map((item) => (
                    <li key={item.key} className="flex items-center justify-between gap-2">
                      <div>
                        <p className="text-[13px] font-medium text-[#111827]">{item.title}</p>
                        <p className="text-[11px] text-[#9ca3af]">{item.description}</p>
                      </div>
                      {toneBadge(item.count_tone, item.count)}
                    </li>
                  ))}
                </ul>
              </section>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#e8ecf2] pt-4 text-[12px] text-[#6b7280] xl:col-span-3">
              <span>{data.form_note}</span>
              <div className="flex gap-2">
                <Link href="/college-admin/academics/grading-system-configuration" className="h-9 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium leading-9 text-[#374151]">
                  {data.cancel_label}
                </Link>
                <button type="button" onClick={handleSave} disabled={save.isPending} className="h-9 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white disabled:opacity-50">
                  {data.save_rules_label}
                </button>
              </div>
            </div>
          </div>
        ) : null}
      </QueryState>
    </div>
  );
}