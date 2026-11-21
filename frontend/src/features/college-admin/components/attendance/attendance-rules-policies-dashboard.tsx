"use client";

import Link from "next/link";
import { useState } from "react";

import { CheckIcon } from "@/components/icons/erp/generated/check";
import { ChevronLeftIcon } from "@/components/icons/erp/generated/chevron-left";
import { XIcon } from "@/components/icons/erp/generated/x";
import { Button } from "@/components/ui/button";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useAttendanceRulesPoliciesPage } from "@/features/college-admin/hooks/use-attendance-configuration";
import { cn } from "@/lib/utils";

function StatusPill({ label, tone }: { label: string; tone: string }) {
  const styles: Record<string, string> = {
    success: "text-[#047857]",
    muted: "text-[#6b7280]",
  };
  const dot: Record<string, string> = {
    success: "bg-[#10b981]",
    muted: "bg-[#9ca3af]",
  };
  const key = tone in styles ? tone : "muted";
  return (
    <span className={cn("inline-flex items-center gap-1.5 text-[13px] font-medium", styles[key])}>
      <span className={cn("size-1.5 rounded-full", dot[key])} />
      {label}
    </span>
  );
}

export function AttendanceRulesPoliciesDashboard() {
  const [page, setPage] = useState(1);
  const queryParams = { page, page_size: 4 };
  const { data, isLoading, isError, error, refetch } = useAttendanceRulesPoliciesPage(queryParams);

  return (
    <div className="space-y-5" data-figma-frame="159:10121">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-2">
          <Link
            href={data?.configuration_href ?? "/college-admin/attendance/attendance-configuration"}
            className="inline-flex items-center gap-1 text-[13px] font-medium text-[#6b7280] hover:text-[#111827]"
          >
            <ChevronLeftIcon className="size-4" aria-hidden />
            {data?.back_label ?? "Back"}
          </Link>
          <div>
            <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
              {data?.page_title ?? "Attendance Rules & Policies"}
            </h2>
            <p className="mt-1 text-[14px] text-[#6b7280]">{data?.page_subtitle ?? "—"}</p>
          </div>
        </div>
        <div className="flex shrink-0 gap-2">
          <Button
            type="button"
            variant="outline"
            className="h-9 gap-1.5 text-xs"
            onClick={() => void refetch()}
          >
            <XIcon className="size-3.5" aria-hidden />
            {data?.cancel_label ?? "Cancel"}
          </Button>
          <Button
            type="button"
            className="h-9 gap-1.5 bg-[#245dd8] text-xs text-white hover:bg-[#1f4fb8]"
            asChild
          >
            <Link href={data?.configuration_href ?? "/college-admin/attendance/attendance-configuration"}>
              <CheckIcon className="size-3.5" aria-hidden />
              {data?.save_label ?? "Save"}
            </Link>
          </Button>
        </div>
      </div>

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.policies_section_title}</h3>
              </div>
              {data.policy_rows.length ? (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[44rem] text-left text-[13px]">
                    <thead>
                      <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                        {data.policies_table_headers.map((header) => (
                          <th key={header} className="px-5 py-3 font-medium">
                            {header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#f1f5f9]">
                      {data.policy_rows.map((row) => (
                        <tr key={row.row_key} className="text-[#111827]">
                          <td className="px-5 py-3.5 font-semibold">{row.policy_title}</td>
                          <td className="px-5 py-3.5">{row.value_label}</td>
                          <td className="px-5 py-3.5 text-[#6b7280]">{row.applies_to_label}</td>
                          <td className="px-5 py-3.5 text-[#6b7280]">{row.effective_label}</td>
                          <td className="px-5 py-3.5">
                            <StatusPill label={row.status_label} tone={row.status_tone} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="px-5 py-8 text-center text-[13px] text-[#6b7280]">No policies configured yet.</p>
              )}
              <div className="flex items-center justify-between border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
                <span>{data.policies_table_footer_label}</span>
                <div className="flex gap-2">
                  <button
                    type="button"
                    disabled={page <= 1}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    className="rounded px-2 py-0.5 hover:bg-[#f3f4f6] disabled:opacity-40"
                  >
                    Prev
                  </button>
                  <button
                    type="button"
                    onClick={() => setPage((p) => p + 1)}
                    className="rounded px-2 py-0.5 hover:bg-[#f3f4f6]"
                  >
                    Next
                  </button>
                </div>
              </div>
            </section>

            <footer className="flex flex-wrap justify-between gap-2 border-t border-[#e8ecf2] pt-4 text-[11px] text-[#9ca3af]">
              <span>{data.footer_disclaimer}</span>
              <span>{data.footer_snapshot_label}</span>
            </footer>
          </>
        ) : null}
      </QueryState>
    </div>
  );
}