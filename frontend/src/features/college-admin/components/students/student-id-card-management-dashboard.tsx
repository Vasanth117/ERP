"use client";

import Link from "next/link";
import { useState } from "react";
import { onCollegeAdminMutationError } from "@/features/college-admin/context/college-admin-validation-context";
import { toast } from "sonner";

import { PlusIcon } from "@/components/icons/erp/generated/plus";
import { Button } from "@/components/ui/button";
import { CollegeAdminDownload } from "@/features/college-admin/components/layout/college-admin-erp-icons";
import {
  CollegeAdminKpiGrid,
  CollegeAdminUserDashboardKpiCard,
} from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useBulkPrintStudentIdCards,
  useIssueStudentIdCard,
  useStudentIdCardManagementPage,
} from "@/features/college-admin/hooks/use-student-id-card-management";
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


export function StudentIdCardManagementDashboard() {
  const [page, setPage] = useState(1);
  const { data, isLoading, isError, error, refetch } = useStudentIdCardManagementPage({ page });
  const issueMutation = useIssueStudentIdCard();
  const bulkPrintMutation = useBulkPrintStudentIdCards();

  const handleBulkPrint = () => {
    bulkPrintMutation.mutate(
      { page },
      {
        onSuccess: () => toast.success("Pending ID cards queued for bulk print."),
        onError: onCollegeAdminMutationError,
      },
    );
  };

  const handleIssueCard = () => {
    issueMutation.mutate(
      { page },
      {
        onSuccess: () => toast.success("ID card issued for the next eligible student."),
        onError: onCollegeAdminMutationError,
      },
    );
  };

  return (
    <div className="space-y-5" data-figma-frame="158:6282">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Student ID Card Management"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">{data?.page_subtitle ?? "Issue, reprint and block ID cards"}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            type="button"
            variant="outline"
            className="h-9 gap-1.5 border-[#dce3ec] text-xs text-[#374151]"
            disabled={bulkPrintMutation.isPending}
            onClick={handleBulkPrint}
          >
            <CollegeAdminDownload className="size-3.5" aria-hidden />
            {data?.bulk_print_label ?? "Bulk print"}
          </Button>
          <Button
            type="button"
            className="h-9 gap-1.5 bg-[#245dd8] text-xs hover:bg-[#1f4fb8]"
            disabled={issueMutation.isPending}
            onClick={handleIssueCard}
          >
            <PlusIcon className="size-3.5" aria-hidden />
            {data?.issue_card_label ?? "Issue card"}
          </Button>
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

            <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="border-b border-[#f1f5f9] bg-[#f9fafb] px-5 py-3.5">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.id_cards_section_title}</h3>
              </div>
              {data.card_rows.length ? (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[40rem] text-left text-[13px]">
                    <thead>
                      <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                        {data.table_headers.map((header, index) => (
                          <th
                            key={header}
                            className={cn(
                              "pb-3 font-medium",
                              index === 0 ? "px-5 pt-4" : "pr-3 pt-4",
                              index === data.table_headers.length - 1 ? "pr-5" : "",
                            )}
                          >
                            {header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#f1f5f9]">
                      {data.card_rows.map((row) => (
                        <tr key={row.record_id} className="text-[#374151]">
                          <td className="px-5 py-3 font-medium text-[#111827]">{row.student_name}</td>
                          <td
                            className={cn(
                              "py-3 pr-3 font-mono text-[12px]",
                              row.card_number_label === "Not issued" ? "text-[#9ca3af]" : "text-[#6b7280]",
                            )}
                          >
                            {row.card_number_label}
                          </td>
                          <td className="py-3 pr-3 text-[#6b7280]">{row.issued_label}</td>
                          <td className="py-3 pr-3 text-[#6b7280]">{row.valid_until_label}</td>
                          <td className="py-3 pr-5">
                            <StatusPill label={row.status_label} tone={row.status_tone} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="px-5 py-10 text-center text-sm text-[#9ca3af]">
                  No students in scope.{" "}
                  <Link href={data.issue_card_href} className="text-[#245dd8] hover:underline">
                    View student list
                  </Link>
                </p>
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

          </>
        ) : null}
      </QueryState>
    </div>
  );
}