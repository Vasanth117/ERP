"use client";

import { useState } from "react";
import { toast } from "sonner";

import { CheckIcon } from "@/components/icons/erp/generated/check";
import { RefreshCwIcon } from "@/components/icons/erp/generated/refresh-cw";
import { Button } from "@/components/ui/button";
import { ExaminationRegistrationSubNav } from "@/features/college-admin/components/examinations/examination-registration-sub-nav";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useAutoAllocateHallSeating,
  useConfirmHallSeating,
  useExaminationHallSeatingManagementPage,
} from "@/features/college-admin/hooks/use-examination-hall-seating-management";
import type { ExaminationHallSeatingManagementPage } from "@/features/college-admin/types/examination-hall-seating-management";
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

function formatSnapshot(iso: string) {
  try {
    return new Intl.DateTimeFormat("en-IN", { dateStyle: "medium", timeStyle: "short", timeZone: "Asia/Kolkata" }).format(new Date(iso));
  } catch {
    return iso;
  }
}

function Pagination({
  data,
  page,
  setPage,
}: {
  data: ExaminationHallSeatingManagementPage;
  page: number;
  setPage: (p: number) => void;
}) {
  return (
    <div className="flex items-center gap-1">
      <button
        type="button"
        className="rounded border border-[#dce3ec] px-2 py-1 disabled:opacity-40"
        disabled={!data.pagination.has_previous}
        onClick={() => setPage(Math.max(1, page - 1))}
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
              num === data.pagination.page ? "border-[#245dd8] bg-[#eff6ff] text-[#245dd8]" : "border-[#dce3ec]",
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
        onClick={() => setPage(page + 1)}
      >
        ›
      </button>
    </div>
  );
}

export function ExaminationHallSeatingManagementDashboard() {
  const [page, setPage] = useState(1);
  const { data, isLoading, isError, error, refetch } = useExaminationHallSeatingManagementPage({ page });
  const autoAllocate = useAutoAllocateHallSeating();
  const confirm = useConfirmHallSeating();

  const payload = () => ({ session_id: data?.selected_session_id ?? "", page });

  const onAutoAllocate = () => {
    if (!data?.selected_session_id) return;
    autoAllocate.mutate(payload(), {
      onSuccess: () => toast.success("Seating auto-allocated."),
      onError: (e: Error) => toast.error(e.message),
    });
  };

  const onConfirm = () => {
    if (!data?.selected_session_id) return;
    confirm.mutate(payload(), {
      onSuccess: () => toast.success("Seating confirmed."),
      onError: (e: Error) => toast.error(e.message),
    });
  };

  return (
    <div className="space-y-5" data-figma-frame="159:13128">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Examination Hall & Seating Management"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">{data?.page_subtitle ?? "Assign halls and generate seating"}</p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <Button
            type="button"
            variant="outline"
            className="h-9 gap-1.5 border-[#dce3ec] text-xs font-medium"
            disabled={autoAllocate.isPending || !data?.selected_session_id}
            onClick={onAutoAllocate}
          >
            <RefreshCwIcon className="size-3.5" aria-hidden />
            {data?.auto_allocate_label ?? "Auto-allocate"}
          </Button>
          <Button
            type="button"
            className="h-9 gap-1.5 bg-[#245dd8] text-xs font-medium hover:bg-[#1f4fb8]"
            disabled={confirm.isPending || !data?.selected_session_id}
            onClick={onConfirm}
          >
            <CheckIcon className="size-3.5" aria-hidden />
            {data?.confirm_label ?? "Confirm"}
          </Button>
        </div>
      </div>

      {data?.sub_nav?.length ? <ExaminationRegistrationSubNav items={data.sub_nav} /> : null}

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            <div className="grid gap-5 lg:grid-cols-[1fr_minmax(14rem,22rem)]">
              <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                  <h3 className="text-[14px] font-semibold text-[#111827]">{data.halls_section_title}</h3>
                </div>
                {data.hall_rows.length ? (
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[36rem] text-left text-[13px]">
                      <thead>
                        <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                          {data.table_headers.map((header, index) => (
                            <th
                              key={header}
                              className={cn("pb-3 font-medium", index === 0 ? "pl-5 pr-3" : "pr-3", index === data.table_headers.length - 1 ? "pr-5" : "")}
                            >
                              {header}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#f1f5f9]">
                        {data.hall_rows.map((row) => (
                          <tr key={row.room_id}>
                            <td className="pl-5 py-3 pr-3 font-medium text-[#111827]">{row.hall_label}</td>
                            <td className="py-3 pr-3 tabular-nums">{row.capacity}</td>
                            <td className="py-3 pr-3 tabular-nums">{row.allocated_count}</td>
                            <td className="py-3 pr-3 tabular-nums">{row.papers_count}</td>
                            <td className="py-3 pr-5">
                              <StatusPill label={row.status_label} tone={row.status_tone} />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="px-5 py-10 text-center text-sm text-[#9ca3af]">No exam halls configured for this session.</p>
                )}
                <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
                  <span>{data.showing_label}</span>
                  {data.pagination.total_pages > 1 ? <Pagination data={data} page={page} setPage={setPage} /> : null}
                </div>
              </section>

              <aside className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.seat_usage_section_title}</h3>
                <ul className="mt-4 space-y-4">
                  {data.seat_usage_items.length ? (
                    data.seat_usage_items.map((item) => (
                      <li key={item.hall_label}>
                        <div className="flex items-baseline justify-between gap-2 text-[13px]">
                          <span className="font-medium text-[#111827]">{item.hall_label}</span>
                          <span className="shrink-0 tabular-nums text-[#6b7280]">{item.usage_label}</span>
                        </div>
                        <div className="mt-2 h-2 overflow-hidden rounded-full bg-[#f3f4f6]">
                          <div
                            className="h-full rounded-full bg-[#a16207]"
                            style={{ width: `${Math.min(100, item.usage_percent)}%` }}
                          />
                        </div>
                      </li>
                    ))
                  ) : (
                    <li className="text-sm text-[#9ca3af]">No seat usage data yet.</li>
                  )}
                </ul>
              </aside>
            </div>

            <footer className="flex flex-col gap-2 border-t border-[#e8ecf2] pt-4 text-[11px] text-[#9ca3af] sm:flex-row sm:items-center sm:justify-between">
              <p>{data.footer_disclaimer}</p>
              <p className="tabular-nums">
                {data.footer_snapshot_label} · {formatSnapshot(data.generated_at)}
              </p>
            </footer>
          </>
        ) : null}
      </QueryState>
    </div>
  );
}