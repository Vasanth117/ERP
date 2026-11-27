"use client";
import { CollegeAdminModulePageHeading } from "@/features/college-admin/components/layout/college-admin-module-page-heading";
import { CollegeAdminPlusActionLabel } from "@/features/college-admin/components/ui/college-admin-plus-action";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { RefreshCwIcon } from "@/components/icons/erp/generated/refresh-cw";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  CollegeAdminPrimaryButton,
  CollegeAdminSecondaryButton,
} from "@/features/college-admin/components/ui/college-admin-action-button";
import {
  CollegeAdminPanelChromeFooter,
  CollegeAdminPanelChromeHeader,
  CollegeAdminPanelShell,
} from "@/features/college-admin/components/ui/dashboard-panel-ui";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useAddBatchSection,
  useAutoAllocateBatchSections,
  useBatchSectionConfigurationPage,
  useSaveBatchSectionRules,
} from "@/features/college-admin/hooks/use-batch-section-configuration";
import type {
  BatchSectionAllocationField,
  BatchSectionConfigurationPage,
} from "@/features/college-admin/types/batch-section-configuration";
import type { InstitutionFieldOption } from "@/features/college-admin/types/institution";
import { cn } from "@/lib/utils";

function StatusPill({ label, tone }: { label: string; tone: string }) {
  const styles: Record<string, string> = {
    success: "bg-[#ecfdf5] text-[#047857]",
    warning: "bg-[#fff7ed] text-[#c2410c]",
    info: "bg-[#eff6ff] text-[#1d4ed8]",
    danger: "bg-[#fef2f2] text-[#b91c1c]",
    muted: "bg-[#f3f4f6] text-[#6b7280]",
  };
  const dot: Record<string, string> = {
    success: "bg-[#10b981]",
    warning: "bg-[#f97316]",
    info: "bg-[#3b82f6]",
    danger: "bg-[#ef4444]",
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

function RuleField({
  field,
  value,
  onChange,
}: {
  field: BatchSectionAllocationField;
  value: string;
  onChange: (next: string) => void;
}) {
  if (field.field_type === "select") {
    return (
      <div>
        <Label className="text-[12px] text-[#374151]">
          {field.label}
          {field.required ? <span className="text-[#dc2626]"> *</span> : null}
        </Label>
        <select
          className="mt-1.5 h-9 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px]"
          value={value}
          onChange={(e) => onChange(e.target.value)}
        >
          {field.options.map((opt: InstitutionFieldOption) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>
    );
  }
  return (
    <div>
      <Label className="text-[12px] text-[#374151]">
        {field.label}
        {field.required ? <span className="text-[#dc2626]"> *</span> : null}
      </Label>
      <Input
        className="mt-1.5 h-9"
        type={field.field_type === "number" ? "number" : "text"}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}

function rulesFromPage(page: BatchSectionConfigurationPage) {
  const out: Record<string, string> = {};
  for (const field of page.allocation_rules.fields) {
    out[field.key] = field.value;
  }
  return out;
}

export function BatchSectionConfigurationDashboard() {
  const router = useRouter();
  const [batchYear, setBatchYear] = useState<string | undefined>();
  const [programmeCode, setProgrammeCode] = useState<string | undefined>();
  const [page, setPage] = useState(1);
  const [showAdd, setShowAdd] = useState(false);

  const [sectionCode, setSectionCode] = useState("");
  const [sectionName, setSectionName] = useState("");
  const [sectionCapacity, setSectionCapacity] = useState("");
  const [sectionRoom, setSectionRoom] = useState("");

  const params = useMemo(
    () => ({ batch_year: batchYear, programme_code: programmeCode, page }),
    [batchYear, programmeCode, page],
  );

  const { data, isLoading, isError, error, refetch } = useBatchSectionConfigurationPage(params);
  const saveRules = useSaveBatchSectionRules();
  const addSection = useAddBatchSection();
  const autoAllocate = useAutoAllocateBatchSections();

  const [ruleValues, setRuleValues] = useState<Record<string, string>>({});

  useEffect(() => {
    if (data?.selected_batch_year) setBatchYear(data.selected_batch_year);
    if (data?.selected_programme_code) setProgrammeCode(data.selected_programme_code);
  }, [data?.selected_batch_year, data?.selected_programme_code]);

  useEffect(() => {
    if (data) setRuleValues(rulesFromPage(data));
  }, [data]);

  const syncQuery = (nextYear: string, nextProgramme?: string, nextPage = 1) => {
    const sp = new URLSearchParams();
    if (nextYear) sp.set("batch_year", nextYear);
    if (nextProgramme) sp.set("programme_code", nextProgramme);
    if (nextPage > 1) sp.set("page", String(nextPage));
    const q = sp.toString();
    router.replace(q ? `?${q}` : "?", { scroll: false });
  };

  const batchLabel = batchYear ? `${batchYear} batch` : "";

  const handleSave = () => {
    saveRules.mutate({
      default_section_size: Number(ruleValues.default_section_size || 60),
      allocation_method: ruleValues.allocation_method || "alphabetical",
      balance_by_gender: ruleValues.balance_by_gender || "yes",
      lateral_entry_handling: ruleValues.lateral_entry_handling || "distribute_existing",
    });
  };

  const handleCancel = () => {
    if (data) setRuleValues(rulesFromPage(data));
  };

  const handleAutoAllocate = () => {
    if (!data?.selected_programme_code || !batchLabel) return;
    autoAllocate.mutate({
      programme_code: data.selected_programme_code,
      batch_label: batchLabel,
    });
  };

  const handleAddSection = () => {
    if (!data?.selected_programme_code || !sectionCode.trim() || !sectionName.trim() || !batchLabel) return;
    addSection.mutate(
      {
        programme_code: data.selected_programme_code,
        batch_label: batchLabel,
        section_code: sectionCode.trim(),
        section_name: sectionName.trim(),
        capacity: Number(sectionCapacity || ruleValues.default_section_size || 60),
        room_label: sectionRoom.trim() || null,
      },
      {
        onSuccess: () => {
          setShowAdd(false);
          setSectionCode("");
          setSectionName("");
          setSectionRoom("");
          setSectionCapacity("");
        },
      },
    );
  };

  const handlePendingAction = (kind: string, href: string | null) => {
    if (kind === "auto_allocate_lateral") {
      handleAutoAllocate();
      return;
    }
    if (kind === "assign_advisor" && href) {
      router.push(href);
    }
  };

  return (
    <div className="space-y-5" data-figma-frame="69:142356">
      <CollegeAdminModulePageHeading title={data?.page_title ?? "Batch & Section Configuration"} subtitle={data?.page_subtitle} actions={<><CollegeAdminSecondaryButton disabled={autoAllocate.isPending} onClick={handleAutoAllocate}>
            <RefreshCwIcon className="size-3.5" aria-hidden />
            {data?.auto_allocate_label ?? "Auto-allocate sections"}
          </CollegeAdminSecondaryButton>
          <CollegeAdminPrimaryButton onClick={() => setShowAdd((v) => !v)}>
            <CollegeAdminPlusActionLabel iconClassName="size-3.5" label={data?.add_section_label ?? "Add section" } />
          </CollegeAdminPrimaryButton></>} />

      {data?.batch_tabs?.length ? (
        <div className="flex flex-wrap gap-2">
          {data.batch_tabs.map((tab) => (
            <button
              key={tab.batch_year}
              type="button"
              onClick={() => {
                setBatchYear(tab.batch_year);
                setPage(1);
                syncQuery(tab.batch_year, programmeCode, 1);
              }}
              className={cn(
                "rounded-full px-4 py-1.5 text-[13px] font-medium transition-colors",
                tab.active || tab.batch_year === batchYear
                  ? "bg-white text-[#111827] shadow-sm ring-1 ring-[#e8ecf2]"
                  : "bg-[#f3f4f6] text-[#6b7280] hover:text-[#374151]",
              )}
            >
              {tab.label}
            </button>
          ))}
        </div>
      ) : null}

      {showAdd && data ? (
        <section className="flex flex-wrap items-end gap-3 rounded-xl border border-[#e8ecf2] bg-white p-4 shadow-sm">
          {data.programme_options.length > 1 ? (
            <div>
              <Label className="text-[12px]">Programme</Label>
              <select
                className="mt-1 h-9 rounded-md border border-[#dce3ec] px-3 text-[13px]"
                value={programmeCode ?? data.selected_programme_code}
                onChange={(e) => {
                  setProgrammeCode(e.target.value);
                  syncQuery(batchYear ?? data.selected_batch_year, e.target.value, page);
                }}
              >
                {data.programme_options.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
          ) : null}
          <div>
            <Label className="text-[12px]">Section code *</Label>
            <Input className="mt-1 h-9 w-24" value={sectionCode} onChange={(e) => setSectionCode(e.target.value)} placeholder="A" />
          </div>
          <div className="min-w-[10rem] flex-1">
            <Label className="text-[12px]">Section name *</Label>
            <Input className="mt-1 h-9" value={sectionName} onChange={(e) => setSectionName(e.target.value)} placeholder="Section A" />
          </div>
          <div>
            <Label className="text-[12px]">Capacity</Label>
            <Input className="mt-1 h-9 w-20" type="number" value={sectionCapacity} onChange={(e) => setSectionCapacity(e.target.value)} placeholder={ruleValues.default_section_size} />
          </div>
          <div>
            <Label className="text-[12px]">Room</Label>
            <Input className="mt-1 h-9 w-24" value={sectionRoom} onChange={(e) => setSectionRoom(e.target.value)} placeholder="C-201" />
          </div>
          <button type="button" disabled={addSection.isPending} onClick={handleAddSection} className="h-9 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white disabled:opacity-50">
            Create section
          </button>
        </section>
      ) : null}

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <div className="grid gap-5 lg:grid-cols-3">
            <div className="space-y-5 lg:col-span-2">
              <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                  <h3 className="text-[14px] font-semibold text-[#111827]">{data.sections_panel_title}</h3>
                </div>
                {data.section_rows.length ? (
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[44rem] text-left text-[13px]">
                      <thead>
                        <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                          {data.table_headers.map((header, index) => (
                            <th key={header} className={cn("pb-3 pt-4 font-medium", index === 0 ? "px-5" : "pr-3", index === data.table_headers.length - 1 ? "pr-5" : "")}>
                              {header}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#f1f5f9]">
                        {data.section_rows.map((row) => (
                          <tr key={row.section_id} className="hover:bg-[#f9fafb]">
                            <td className="px-5 py-3 font-medium text-[#111827]">{row.section_label}</td>
                            <td className="py-3 pr-3">{row.advisor_label}</td>
                            <td className="py-3 pr-3 tabular-nums">{row.capacity_label}</td>
                            <td className="py-3 pr-3 tabular-nums">{row.allocated_count ?? "—"}</td>
                            <td className="py-3 pr-3">{row.room_label}</td>
                            <td className="py-3 pr-5">
                              <StatusPill label={row.status_label} tone={row.status_tone} />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="px-5 py-10 text-sm text-[#9ca3af]">No sections configured for this batch yet.</p>
                )}
                <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
                  <span>{data.section_summary_label}</span>
                  {data.pagination.total_pages > 0 ? (
                    <div className="flex items-center gap-1">
                      <button
                        type="button"
                        className="rounded border border-[#dce3ec] px-2 py-1 disabled:opacity-40"
                        disabled={!data.pagination.has_previous}
                        onClick={() => {
                          const next = Math.max(1, page - 1);
                          setPage(next);
                          syncQuery(batchYear ?? data.selected_batch_year, programmeCode, next);
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
                              syncQuery(batchYear ?? data.selected_batch_year, programmeCode, num);
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
                          syncQuery(batchYear ?? data.selected_batch_year, programmeCode, next);
                        }}
                      >
                        ›
                      </button>
                    </div>
                  ) : null}
                </div>
              </section>

              <CollegeAdminPanelShell>
                <CollegeAdminPanelChromeHeader title={data.allocation_rules.section_title} />
                <div className="grid gap-4 px-5 py-4 sm:grid-cols-2">
                  {data.allocation_rules.fields.map((field) => (
                    <RuleField
                      key={field.key}
                      field={field}
                      value={ruleValues[field.key] ?? field.value}
                      onChange={(next) => setRuleValues((prev) => ({ ...prev, [field.key]: next }))}
                    />
                  ))}
                </div>
                <CollegeAdminPanelChromeFooter className="flex-col gap-3 sm:flex-row sm:items-center">
                  <p className="text-[12px] font-normal text-[#64748b]">{data.footer_note}</p>
                  <div className="flex shrink-0 gap-2 sm:ml-auto">
                    <CollegeAdminSecondaryButton onClick={handleCancel}>{data.cancel_label}</CollegeAdminSecondaryButton>
                    <CollegeAdminPrimaryButton disabled={saveRules.isPending} onClick={handleSave}>
                      {data.save_label}
                    </CollegeAdminPrimaryButton>
                  </div>
                </CollegeAdminPanelChromeFooter>
              </CollegeAdminPanelShell>
            </div>

            <div className="flex flex-col gap-5">
              <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.overview_title}</h3>
                <div className="mt-4 space-y-4">
                  {data.overview_rows.map((row) => (
                    <div key={row.batch_label}>
                      <div className="mb-1.5 flex items-center justify-between text-[12px]">
                        <span className="font-medium text-[#374151]">{row.batch_label}</span>
                        <span className="text-[#6b7280]">{row.seats_filled_label}</span>
                      </div>
                      <div className="h-2 overflow-hidden rounded-full bg-[#e8ecf2]">
                        <div className="h-full rounded-full bg-[#245dd8]" style={{ width: `${row.bar_percent}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </section>

              <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.pending_tasks_title}</h3>
                <ul className="mt-3 space-y-3">
                  {data.pending_tasks.map((task) => (
                    <li key={task.task_id} className="flex items-start justify-between gap-3 border-b border-[#f1f5f9] pb-3 last:border-0 last:pb-0">
                      <div>
                        <p className="text-[13px] font-medium text-[#111827]">{task.title}</p>
                        <p className="text-[12px] text-[#6b7280]">{task.subtitle}</p>
                      </div>
                      <button
                        type="button"
                        onClick={() => handlePendingAction(task.action_kind, task.action_href)}
                        className={cn(
                          "shrink-0 rounded-md border px-2.5 py-1 text-[11px] font-medium",
                          task.status_tone === "danger"
                            ? "border-[#fecaca] text-[#b91c1c] hover:bg-[#fef2f2]"
                            : "border-[#fde68a] text-[#b45309] hover:bg-[#fffbeb]",
                        )}
                      >
                        {task.action_label}
                      </button>
                    </li>
                  ))}
                  {!data.pending_tasks.length ? <li className="text-[12px] text-[#9ca3af]">No pending tasks.</li> : null}
                </ul>
              </section>
            </div>
          </div>
        ) : null}
      </QueryState>

    </div>
  );
}