"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { CheckIcon } from "@/components/icons/erp/generated/check";
import { EyeIcon } from "@/components/icons/erp/generated/eye";
import { Input } from "@/components/ui/input";
import { CreditGradingSubNav } from "@/features/college-admin/components/academics/credit-grading-sub-nav";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useGradingSystemConfigurationPage,
  useSaveGradingSystemConfiguration,
} from "@/features/college-admin/hooks/use-credit-grading";
import type { GradingClassificationRow, GradingScaleRow, RuleToggle } from "@/features/college-admin/types/credit-grading";
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

export function GradingSystemConfigurationDashboard() {
  const { data, isLoading, isError, error, refetch } = useGradingSystemConfigurationPage();
  const save = useSaveGradingSystemConfiguration();

  const [grades, setGrades] = useState<GradingScaleRow[]>([]);
  const [classes, setClasses] = useState<GradingClassificationRow[]>([]);
  const [calc, setCalc] = useState<Record<string, string>>({});
  const [rules, setRules] = useState<Record<string, boolean>>({});

  useEffect(() => {
    if (!data) return;
    setGrades(data.grade_rows.map((r) => ({ ...r })));
    setClasses(data.classification_rows.map((r) => ({ ...r })));
    const c: Record<string, string> = {};
    for (const field of data.calculation_fields) c[field.key] = field.value;
    setCalc(c);
    const r: Record<string, boolean> = {};
    for (const rule of data.rules) r[rule.key] = rule.enabled;
    setRules(r);
  }, [data]);

  const handleSave = () => {
    if (!data) return;
    save.mutate({ grade_rows: grades, classification_rows: classes, calculation: calc, rules });
  };

  return (
    <div className="space-y-5" data-figma-frame="69:141649">
      {data?.sub_nav.length ? <CreditGradingSubNav items={data.sub_nav} /> : null}

      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold text-[#111827]">{data?.page_title ?? "Grading System Configuration"}</h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">{data?.page_subtitle}</p>
        </div>
        <div className="flex gap-2">
          <Link
            href={data?.preview_transcript_href ?? "/college-admin/examinations"}
            className="inline-flex h-9 items-center gap-1.5 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151]"
          >
            <EyeIcon className="size-3.5" />
            {data?.preview_transcript_label ?? "Preview transcript"}
          </Link>
          <button
            type="button"
            onClick={handleSave}
            disabled={save.isPending}
            className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white"
          >
            <CheckIcon className="size-3.5" />
            {data?.save_grading_label ?? "Save grading"}
          </button>
        </div>
      </div>

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <div className="grid gap-5 xl:grid-cols-3">
            <div className="space-y-5 xl:col-span-2">
              <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-sm">
                <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                  <h3 className="text-[14px] font-semibold text-[#111827]">{data.grade_scale_title}</h3>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[36rem] text-left text-[13px]">
                    <thead>
                      <tr className="text-[11px] uppercase tracking-wide text-[#9ca3af]">
                        {data.grade_table_headers.map((h, i) => (
                          <th key={h} className={cn("pb-3 pt-4 font-medium", i === 0 ? "px-5" : "pr-3")}>
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#f1f5f9]">
                      {grades.map((row, index) => (
                        <tr key={row.grade_id}>
                          <td className="px-5 py-2 font-semibold">{row.grade}</td>
                          <td className="py-2 pr-3">
                            <Input
                              className="h-8 w-14 tabular-nums"
                              type="number"
                              value={row.grade_point}
                              onChange={(e) =>
                                setGrades((prev) => {
                                  const next = [...prev];
                                  next[index] = { ...row, grade_point: Number(e.target.value) };
                                  return next;
                                })
                              }
                            />
                          </td>
                          <td className="py-2 pr-3">
                            <Input
                              className="h-8 min-w-[6rem]"
                              value={row.marks_range_label}
                              onChange={(e) =>
                                setGrades((prev) => {
                                  const next = [...prev];
                                  next[index] = { ...row, marks_range_label: e.target.value };
                                  return next;
                                })
                              }
                            />
                          </td>
                          <td className="py-2 pr-5">
                            <Input
                              className="h-8"
                              value={row.description}
                              onChange={(e) =>
                                setGrades((prev) => {
                                  const next = [...prev];
                                  next[index] = { ...row, description: e.target.value };
                                  return next;
                                })
                              }
                            />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="flex justify-between border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
                  <span>{data.grade_scale_footer}</span>
                  <span className="text-[#245dd8]">{data.add_grade_label}</span>
                </div>
              </section>

              <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-sm">
                <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                  <h3 className="text-[14px] font-semibold text-[#111827]">{data.classification_section_title}</h3>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-[13px]">
                    <thead>
                      <tr className="text-[11px] uppercase tracking-wide text-[#9ca3af]">
                        {data.classification_table_headers.map((h, i) => (
                          <th key={h} className={cn("pb-3 pt-4 font-medium", i === 0 ? "px-5" : "pr-3")}>
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#f1f5f9]">
                      {classes.map((row, index) => (
                        <tr key={row.class_id}>
                          <td className="px-5 py-2">
                            <Input className="h-8" value={row.class_label} onChange={(e) => setClasses((p) => p.map((r, i) => (i === index ? { ...r, class_label: e.target.value } : r)))} />
                          </td>
                          <td className="py-2 pr-3">
                            <Input className="h-8" value={row.cgpa_label} onChange={(e) => setClasses((p) => p.map((r, i) => (i === index ? { ...r, cgpa_label: e.target.value } : r)))} />
                          </td>
                          <td className="py-2 pr-5">
                            <Input className="h-8" value={row.condition_label} onChange={(e) => setClasses((p) => p.map((r, i) => (i === index ? { ...r, condition_label: e.target.value } : r)))} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="flex justify-between border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
                  <span>{data.classification_footer}</span>
                  <span className="text-[#245dd8]">{data.classification_edit_label}</span>
                </div>
              </section>
            </div>

            <div className="space-y-4">
              <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-sm">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.calculation_section_title}</h3>
                <div className="mt-4 space-y-4">
                  {data.calculation_fields.map((field) => (
                    <div key={field.key}>
                      <label className="text-[12px] text-[#374151]">
                        {field.label}
                        {field.required ? " *" : ""}
                      </label>
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
                    </div>
                  ))}
                </div>
              </section>
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
            </div>

            <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#e8ecf2] pt-4 text-[12px] text-[#6b7280] xl:col-span-3">
              <span>{data.form_note}</span>
              <div className="flex gap-2">
                <Link href="/college-admin/academics/credit-configuration" className="h-9 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium leading-9 text-[#374151]">
                  {data.cancel_label}
                </Link>
                <button type="button" onClick={handleSave} disabled={save.isPending} className="h-9 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white disabled:opacity-50">
                  {data.save_grading_label}
                </button>
              </div>
            </div>
          </div>
        ) : null}
      </QueryState>
    </div>
  );
}