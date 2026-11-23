"use client";

import { useState } from "react";
import { toast } from "sonner";

import { ClockIcon } from "@/components/icons/erp/generated/clock";
import { SendIcon } from "@/components/icons/erp/generated/send";
import { TriangleAlertIcon } from "@/components/icons/erp/generated/triangle-alert";
import { Button } from "@/components/ui/button";
import { ExaminationRegistrationSubNav } from "@/features/college-admin/components/examinations/examination-registration-sub-nav";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  usePublishResultsNow,
  useResultPublicationPage,
  useScheduleResultPublication,
} from "@/features/college-admin/hooks/use-result-publication";
import type { ResultPublicationPage } from "@/features/college-admin/types/result-publication";
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
    <span className={cn("inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-medium", styles[key])}>
      <span className={cn("size-1.5 rounded-full", dot[key])} />
      {label}
    </span>
  );
}


function Pagination({ data, page, setPage }: { data: ResultPublicationPage; page: number; setPage: (p: number) => void }) {
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

export function ResultPublicationDashboard() {
  const [page, setPage] = useState(1);
  const { data, isLoading, isError, error, refetch } = useResultPublicationPage({ page });
  const publishNow = usePublishResultsNow();
  const schedule = useScheduleResultPublication();

  const payload = () => ({ session_id: data?.selected_session_id ?? "", page });

  return (
    <div className="space-y-5" data-figma-frame="CA-09-result-publication">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">{data?.page_title ?? "Result Publication"}</h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">{data?.page_subtitle ?? "Publish approved results"}</p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <Button
            type="button"
            variant="outline"
            className="h-9 gap-1.5 border-[#dce3ec] text-xs font-medium"
            disabled={schedule.isPending || !data?.selected_session_id}
            onClick={() =>
              schedule.mutate(payload(), {
                onSuccess: () => toast.success("Publication scheduled."),
                onError: (e: Error) => toast.error(e.message),
              })
            }
          >
            <ClockIcon className="size-3.5" aria-hidden />
            {data?.schedule_label ?? "Schedule"}
          </Button>
          <Button
            type="button"
            className="h-9 gap-1.5 bg-[#245dd8] text-xs font-medium hover:bg-[#1f4fb8]"
            disabled={publishNow.isPending || !data?.selected_session_id}
            onClick={() =>
              publishNow.mutate(payload(), {
                onSuccess: () => toast.success("Results published."),
                onError: (e: Error) => toast.error(e.message),
              })
            }
          >
            <SendIcon className="size-3.5" aria-hidden />
            {data?.publish_now_label ?? "Publish now"}
          </Button>
        </div>
      </div>

      {data?.sub_nav?.length ? <ExaminationRegistrationSubNav items={data.sub_nav} /> : null}

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            <div className="flex gap-3 rounded-lg border border-[#fde68a] bg-[#fffbeb] px-4 py-3 text-[#92400e]">
              <TriangleAlertIcon className="mt-0.5 size-4 shrink-0" aria-hidden />
              <div>
                <p className="text-[13px] font-semibold text-[#78350f]">{data.warning_title}</p>
                <p className="mt-0.5 text-[12px] text-[#92400e]">{data.warning_message}</p>
              </div>
            </div>

            <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="flex items-center justify-between border-b border-[#f1f5f9] px-5 py-3.5">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.ready_section_title}</h3>
                <span className="text-[12px] text-[#6b7280]">{data.ready_count_label}</span>
              </div>
              {data.programme_rows.length ? (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[44rem] text-left text-[13px]">
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
                          <td className="py-3 pr-3 text-[#6b7280]">{row.approved_label}</td>
                          <td className="py-3 pr-3 text-[#6b7280]">{row.publish_at_label}</td>
                          <td className="py-3 pr-5">
                            <StatusPill label={row.notify_label} tone={row.notify_tone} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="px-5 py-10 text-center text-sm text-[#9ca3af]">No programmes ready for publication yet.</p>
              )}
              <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
                <span>{data.showing_label}</span>
                {data.pagination.total_pages > 1 ? <Pagination data={data} page={page} setPage={setPage} /> : null}
              </div>
            </section>

          </>
        ) : null}
      </QueryState>
    </div>
  );
}