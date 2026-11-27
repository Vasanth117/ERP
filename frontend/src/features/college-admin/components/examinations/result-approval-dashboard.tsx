"use client";

import { useState } from "react";
import { onCollegeAdminMutationError } from "@/features/college-admin/context/college-admin-validation-context";
import { CollegeAdminModulePageHeading } from "@/features/college-admin/components/layout/college-admin-module-page-heading";
import { toast } from "sonner";

import { CheckIcon } from "@/components/icons/erp/generated/check";
import { ChevronLeftIcon } from "@/components/icons/erp/generated/chevron-left";
import { Button } from "@/components/ui/button";
import { ExaminationRegistrationSubNav } from "@/features/college-admin/components/examinations/examination-registration-sub-nav";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useApproveResultApproval,
  useResultApprovalPage,
  useReturnResultApproval,
} from "@/features/college-admin/hooks/use-result-approval";
import type { ResultApprovalPage } from "@/features/college-admin/types/result-approval";
import { cn } from "@/lib/utils";


function ApprovalTimeline({
  title,
  steps,
}: {
  title: string;
  steps: { key: string; title: string; status_label: string; status_tone: string }[];
}) {
  return (
    <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
      <div className="border-b border-[#f1f5f9] px-5 py-3.5">
        <h3 className="text-[14px] font-semibold text-[#111827]">{title}</h3>
      </div>
      <ol className="space-y-0 px-5 py-4">
        {steps.map((step, index) => (
          <li key={step.key} className="relative flex gap-3 pb-5 last:pb-0">
            {index < steps.length - 1 ? (
              <span className="absolute left-[5px] top-3 h-[calc(100%-4px)] w-px bg-[#e5e7eb]" aria-hidden />
            ) : null}
            <span
              className={cn(
                "relative z-[1] mt-1 size-2.5 shrink-0 rounded-full ring-4 ring-white",
                step.status_tone === "success"
                  ? "bg-[#10b981]"
                  : step.status_tone === "warning"
                    ? "bg-[#f97316]"
                    : step.status_tone === "info"
                      ? "bg-[#3b82f6]"
                      : "bg-[#d1d5db]",
              )}
            />
            <div>
              <p className="text-[13px] font-medium text-[#111827]">{step.title}</p>
              <p className="text-[12px] text-[#6b7280]">{step.status_label}</p>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}

function Pagination({ data, page, setPage }: { data: ResultApprovalPage; page: number; setPage: (p: number) => void }) {
  return (
    <div className="flex items-center gap-1">
      <button type="button" className="rounded border border-[#dce3ec] px-2 py-1 disabled:opacity-40" disabled={!data.pagination.has_previous} onClick={() => setPage(Math.max(1, page - 1))}>
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
            className={cn("min-w-8 rounded border px-2 py-1 tabular-nums", num === data.pagination.page ? "border-[#245dd8] bg-[#eff6ff] text-[#245dd8]" : "border-[#dce3ec]")}
            onClick={() => setPage(num)}
          >
            {num}
          </button>
        ),
      )}
      <button type="button" className="rounded border border-[#dce3ec] px-2 py-1 disabled:opacity-40" disabled={!data.pagination.has_next} onClick={() => setPage(page + 1)}>
        ›
      </button>
    </div>
  );
}

export function ResultApprovalDashboard() {
  const [page, setPage] = useState(1);
  const { data, isLoading, isError, error, refetch } = useResultApprovalPage({ page });
  const approve = useApproveResultApproval();
  const returnForCorrections = useReturnResultApproval();

  const payload = () => ({ session_id: data?.selected_session_id ?? "", page });

  return (
    <div className="space-y-5" data-figma-frame="CA-09-result-approval">
      <CollegeAdminModulePageHeading title={data?.page_title ?? "Result Approval"} subtitle={data?.page_subtitle ?? "Approve processed results before publishing"} actions={<><Button
            type="button"
            variant="outline"
            className="h-9 gap-1.5 border-[#dce3ec] text-xs font-medium"
            disabled={returnForCorrections.isPending || !data?.selected_session_id}
            onClick={() =>
              returnForCorrections.mutate(payload(), {
                onSuccess: () => toast.success("Results returned for corrections."),
                onError: onCollegeAdminMutationError,
              })
            }
          >
            <ChevronLeftIcon className="size-3.5" aria-hidden />
            {data?.return_label ?? "Return"}
          </Button>
          <Button
            type="button"
            className="h-9 gap-1.5 bg-[#245dd8] text-xs font-medium hover:bg-[#1f4fb8]"
            disabled={approve.isPending || !data?.selected_session_id}
            onClick={() =>
              approve.mutate(payload(), {
                onSuccess: () => toast.success("Results approved."),
                onError: onCollegeAdminMutationError,
              })
            }
          >
            <CheckIcon className="size-3.5" aria-hidden />
            {data?.approve_label ?? "Approve"}
          </Button></>} />

      {data?.sub_nav?.length ? <ExaminationRegistrationSubNav items={data.sub_nav} /> : null}

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(16rem,22rem)]">
              <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                  <h3 className="text-[14px] font-semibold text-[#111827]">{data.summary_section_title}</h3>
                </div>
                {data.programme_rows.length ? (
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[28rem] text-left text-[13px]">
                      <thead>
                        <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                          {data.table_headers.map((header, index) => (
                            <th key={header} className={cn("pb-3 font-medium", index === 0 ? "pl-5 pr-3" : "pr-3", index === data.table_headers.length - 1 ? "pr-5" : "")}>
                              {header}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#f1f5f9]">
                        {data.programme_rows.map((row) => (
                          <tr key={row.programme_code}>
                            <td className="pl-5 py-3 pr-3 font-medium text-[#111827]">{row.programme_label}</td>
                            <td className="py-3 pr-3 tabular-nums">{row.students_count.toLocaleString("en-IN")}</td>
                            <td className="py-3 pr-3 tabular-nums">{row.pass_count.toLocaleString("en-IN")}</td>
                            <td className="py-3 pr-5 tabular-nums">{row.pass_percent_label}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="px-5 py-10 text-center text-sm text-[#9ca3af]">No programme summaries yet.</p>
                )}
                <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
                  <span>{data.showing_label}</span>
                  {data.pagination.total_pages > 1 ? <Pagination data={data} page={page} setPage={setPage} /> : null}
                </div>
              </section>

              <ApprovalTimeline title={data.route_section_title} steps={data.approval_route_steps} />
            </div>

          </>
        ) : null}
      </QueryState>
    </div>
  );
}