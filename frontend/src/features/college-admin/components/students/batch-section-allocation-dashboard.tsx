"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { onCollegeAdminMutationError } from "@/features/college-admin/context/college-admin-validation-context";
import { toast } from "sonner";

import { CheckIcon } from "@/components/icons/erp/generated/check";
import { RefreshCwIcon } from "@/components/icons/erp/generated/refresh-cw";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useAutoAllocateBatchSections,
  useBatchSectionAllocationPage,
  useConfirmBatchSectionAllocation,
} from "@/features/college-admin/hooks/use-batch-section-allocation";
import type { BatchSectionAllocationField } from "@/features/college-admin/types/batch-section-configuration";
import type { InstitutionFieldOption } from "@/features/college-admin/types/institution";
import { cn } from "@/lib/utils";

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
        <Label className="text-[12px] font-medium text-[#374151]">
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
      <Label className="text-[12px] font-medium text-[#374151]">
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

function MiniPager({
  pagination,
  onPage,
}: {
  pagination: {
    page: number;
    total_pages: number;
    has_previous: boolean;
    has_next: boolean;
  };
  onPage: (page: number) => void;
}) {
  if (pagination.total_pages <= 1) return null;
  return (
    <div className="flex items-center gap-1">
      <button
        type="button"
        className="rounded border border-[#dce3ec] px-2 py-0.5 text-[11px] disabled:opacity-40"
        disabled={!pagination.has_previous}
        onClick={() => onPage(pagination.page - 1)}
      >
        ‹
      </button>
      <span className="tabular-nums text-[11px] text-[#6b7280]">
        {pagination.page} / {pagination.total_pages}
      </span>
      <button
        type="button"
        className="rounded border border-[#dce3ec] px-2 py-0.5 text-[11px] disabled:opacity-40"
        disabled={!pagination.has_next}
        onClick={() => onPage(pagination.page + 1)}
      >
        ›
      </button>
    </div>
  );
}


export function BatchSectionAllocationDashboard() {
  const [sectionPage, setSectionPage] = useState(1);
  const [unallocatedPage, setUnallocatedPage] = useState(1);
  const [ruleValues, setRuleValues] = useState<Record<string, string>>({});

  const { data, isLoading, isError, error, refetch } = useBatchSectionAllocationPage({
    section_page: sectionPage,
    unallocated_page: unallocatedPage,
  });

  const autoAllocate = useAutoAllocateBatchSections();
  const confirmMutation = useConfirmBatchSectionAllocation();

  useEffect(() => {
    if (!data?.allocation_rules_fields?.length) return;
    const next: Record<string, string> = {};
    for (const field of data.allocation_rules_fields) {
      next[field.key] = field.value;
    }
    setRuleValues(next);
  }, [data?.allocation_rules_fields]);

  const rulesPayload = () => ({
    allocation_method: ruleValues.allocation_method ?? "alphabetical_balanced",
    max_per_section: Number(ruleValues.default_section_size ?? 65),
    keep_groups_together: ruleValues.keep_groups_together ?? "hostel_blocks",
    section_page: sectionPage,
    unallocated_page: unallocatedPage,
  });

  const handleAutoAllocate = () => {
    autoAllocate.mutate(
      { section_page: sectionPage, unallocated_page: unallocatedPage },
      {
        onSuccess: () => toast.success("Students auto-allocated to open sections."),
        onError: onCollegeAdminMutationError,
      },
    );
  };

  const handleConfirm = () => {
    confirmMutation.mutate(rulesPayload(), {
      onSuccess: () => toast.success("Allocation rules confirmed."),
      onError: onCollegeAdminMutationError,
    });
  };

  return (
    <div className="space-y-5" data-figma-frame="158:4860">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Batch & Section Allocation"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">
            {data?.page_subtitle ?? "Allocate students to sections"}
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <Button
            type="button"
            variant="outline"
            className="h-9 gap-1.5 border-[#dce3ec] text-xs font-medium text-[#374151]"
            onClick={handleAutoAllocate}
            disabled={isLoading || autoAllocate.isPending}
          >
            <RefreshCwIcon className="size-3.5" aria-hidden />
            {data?.auto_allocate_label ?? "Auto-allocate"}
          </Button>
          <Button
            type="button"
            className="h-9 gap-1.5 bg-[#245dd8] text-xs font-medium text-white hover:bg-[#1f4fb8]"
            onClick={handleConfirm}
            disabled={isLoading || confirmMutation.isPending}
          >
            <CheckIcon className="size-3.5" aria-hidden />
            {data?.confirm_label ?? "Confirm"}
          </Button>
        </div>
      </div>

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_300px]">
            <div className="space-y-5">
              <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <div className="flex items-center justify-between border-b border-[#f1f5f9] px-5 py-3.5">
                  <h3 className="text-[14px] font-semibold text-[#111827]">{data.section_strength_title}</h3>
                  <MiniPager pagination={data.section_pagination} onPage={setSectionPage} />
                </div>
                {data.section_rows.length ? (
                  <table className="w-full min-w-[36rem] text-left text-[13px]">
                    <thead>
                      <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                        {data.section_table_headers.map((header, index) => (
                          <th
                            key={header}
                            className={cn(
                              "pb-3 font-medium",
                              index === 0 ? "px-5" : "pr-3",
                              index === data.section_table_headers.length - 1 ? "pr-5" : "",
                            )}
                          >
                            {header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#f1f5f9]">
                      {data.section_rows.map((row) => (
                        <tr key={row.section_id} className="text-[#374151]">
                          <td className="px-5 py-3 font-medium text-[#111827]">{row.section_label}</td>
                          <td className="py-3 pr-3">{row.programme_label}</td>
                          <td className="py-3 pr-3 tabular-nums">{row.semester_label}</td>
                          <td className="py-3 pr-3 tabular-nums">{row.strength_count}</td>
                          <td className="py-3 pr-3 tabular-nums">{row.capacity_count}</td>
                          <td className="py-3 pr-5">
                            <StatusPill label={row.status_label} tone={row.status_tone} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <p className="px-5 py-8 text-sm text-[#9ca3af]">No active sections configured yet.</p>
                )}
                <div className="border-t border-[#f1f5f9] px-5 py-2.5 text-[12px] text-[#6b7280]">
                  {data.section_summary_label}
                </div>
              </section>

              <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <div className="flex items-center justify-between border-b border-[#f1f5f9] px-5 py-3.5">
                  <h3 className="text-[14px] font-semibold text-[#111827]">{data.unallocated_title}</h3>
                  <MiniPager pagination={data.unallocated_pagination} onPage={setUnallocatedPage} />
                </div>
                {data.unallocated_rows.length ? (
                  <table className="w-full min-w-[28rem] text-left text-[13px]">
                    <thead>
                      <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                        {data.unallocated_table_headers.map((header, index) => (
                          <th
                            key={header}
                            className={cn(
                              "pb-3 font-medium",
                              index === 0 ? "px-5" : "pr-3",
                              index === data.unallocated_table_headers.length - 1 ? "pr-5" : "",
                            )}
                          >
                            {header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#f1f5f9]">
                      {data.unallocated_rows.map((row) => (
                        <tr key={row.record_id} className="text-[#374151]">
                          <td className="px-5 py-3 font-medium text-[#111827]">
                            <Link href={row.detail_href} className="hover:text-[#245dd8]">
                              {row.student_name}
                            </Link>
                          </td>
                          <td className="py-3 pr-3 font-mono text-[12px] text-[#6b7280]">{row.register_number}</td>
                          <td className="py-3 pr-5">{row.programme_label}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <p className="px-5 py-8 text-sm text-[#9ca3af]">All eligible students have section assignments.</p>
                )}
                <div className="border-t border-[#f1f5f9] px-5 py-2.5 text-[12px] text-[#6b7280]">
                  {data.unallocated_summary_label}
                </div>
              </section>
            </div>

            <aside className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.allocation_rules_title}</h3>
              </div>
              <div className="space-y-4 px-5 py-5">
                {data.allocation_rules_fields.map((field) => (
                  <RuleField
                    key={field.key}
                    field={field}
                    value={ruleValues[field.key] ?? field.value}
                    onChange={(v) => setRuleValues((prev) => ({ ...prev, [field.key]: v }))}
                  />
                ))}
              </div>
            </aside>
          </div>
        ) : null}
      </QueryState>
    </div>
  );
}