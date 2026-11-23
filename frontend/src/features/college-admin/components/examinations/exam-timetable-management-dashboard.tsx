"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";

import { FilterIcon } from "@/components/icons/erp/generated/filter";
import { RefreshCwIcon } from "@/components/icons/erp/generated/refresh-cw";
import { SendIcon } from "@/components/icons/erp/generated/send";
import { TriangleAlertIcon } from "@/components/icons/erp/generated/triangle-alert";
import { Button } from "@/components/ui/button";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useExamTimetableManagementPage,
  usePublishExamTimetable,
  useRegenerateExamTimetable,
} from "@/features/college-admin/hooks/use-exam-timetable-management";
import { cn } from "@/lib/utils";

function FilterSelect({
  icon,
  label,
  value,
  onChange,
  options,
}: {
  icon?: React.ReactNode;
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <div className="relative">
      {icon ? (
        <span className="pointer-events-none absolute left-3 top-1/2 z-[1] -translate-y-1/2 text-[#9ca3af]">
          {icon}
        </span>
      ) : null}
      <select
        aria-label={label}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={cn(
          "h-9 min-w-[9rem] max-w-[20rem] rounded-md border border-[#dce3ec] bg-white pr-8 text-[13px] text-[#374151]",
          icon ? "pl-9" : "pl-3",
        )}
      >
        {options.map((opt) => (
          <option key={`${opt.value}-${opt.label}`} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
}


export function ExamTimetableManagementDashboard() {
  const [page, setPage] = useState(1);
  const [sessionId, setSessionId] = useState("");
  const [programme, setProgramme] = useState("");

  useEffect(() => {
    setPage(1);
  }, [sessionId, programme]);

  const { data, isLoading, isError, error, refetch } = useExamTimetableManagementPage({
    page,
    session_id: sessionId || undefined,
    programme_code: programme || undefined,
  });

  const regenerate = useRegenerateExamTimetable();
  const publish = usePublishExamTimetable();

  useEffect(() => {
    if (data?.selected_session_id && !sessionId) {
      setSessionId(data.selected_session_id);
    }
  }, [data?.selected_session_id, sessionId]);

  const actionPayload = () => ({
    session_id: data?.selected_session_id ?? sessionId,
    programme_code: programme || undefined,
    page,
  });

  const handleRegenerate = () => {
    if (!data?.selected_session_id) return;
    regenerate.mutate(actionPayload(), {
      onSuccess: () => toast.success("Timetable regenerated."),
      onError: (e: Error) => toast.error(e.message),
    });
  };

  const handlePublish = () => {
    if (!data?.selected_session_id) return;
    publish.mutate(actionPayload(), {
      onSuccess: () => toast.success("Timetable published."),
      onError: (e: Error) => toast.error(e.message),
    });
  };

  return (
    <div className="space-y-5" data-figma-frame="159:11789">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Exam Timetable Management"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">{data?.page_subtitle ?? "—"}</p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <Button
            type="button"
            variant="outline"
            className="h-9 gap-1.5 border-[#dce3ec] text-xs font-medium"
            disabled={regenerate.isPending || !data?.selected_session_id}
            onClick={handleRegenerate}
          >
            <RefreshCwIcon className="size-3.5" aria-hidden />
            {data?.regenerate_label ?? "Regenerate"}
          </Button>
          <Button
            type="button"
            className="h-9 gap-1.5 bg-[#245dd8] text-xs font-medium hover:bg-[#1f4fb8]"
            disabled={publish.isPending || !data?.publish_enabled}
            onClick={handlePublish}
          >
            <SendIcon className="size-3.5" aria-hidden />
            {data?.publish_label ?? "Publish"}
          </Button>
        </div>
      </div>

      <p className="text-[12px] text-[#9ca3af]">
        {data?.timetable_status_label ? `Status · ${data.timetable_status_label}` : null}
      </p>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <FilterSelect
            label={data?.session_filter_label ?? "Exam session"}
            value={sessionId}
            onChange={setSessionId}
            options={data?.session_options ?? []}
          />
          <FilterSelect
            icon={<FilterIcon className="size-3.5" aria-hidden />}
            label={data?.programme_filter_label ?? "Programme"}
            value={programme}
            onChange={setProgramme}
            options={data?.programme_options ?? [{ value: "", label: "All programmes" }]}
          />
        </div>
      </div>

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            {data.clash_banner.visible ? (
              <div className="flex gap-3 rounded-lg border border-[#fde68a] bg-[#fffbeb] px-4 py-3 text-[#92400e]">
                <TriangleAlertIcon className="mt-0.5 size-4 shrink-0" aria-hidden />
                <div>
                  <p className="text-[13px] font-semibold text-[#78350f]">{data.clash_banner.headline}</p>
                  <p className="mt-0.5 text-[12px] text-[#92400e]">{data.clash_banner.description}</p>
                </div>
              </div>
            ) : null}

            <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.timetable_section_title}</h3>
              </div>
              {data.rows.length ? (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[48rem] text-left text-[13px]">
                    <thead>
                      <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                        {data.table_headers.map((header, index) => (
                          <th
                            key={header}
                            className={cn(
                              "pb-3 font-medium",
                              index === 0 ? "pl-5 pr-3" : "pr-3",
                              index === data.table_headers.length - 1 ? "pr-5" : "",
                            )}
                          >
                            {header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#f1f5f9]">
                      {data.rows.map((row) => (
                        <tr key={row.entry_code} className="text-[#374151]">
                          <td className="pl-5 py-3 pr-3 text-[#6b7280]">{row.date_label}</td>
                          <td className="py-3 pr-3 font-medium text-[#111827]">{row.session_label}</td>
                          <td className="py-3 pr-3 font-medium text-[#111827]">{row.subject_label}</td>
                          <td className="py-3 pr-3 tabular-nums">{row.code_label}</td>
                          <td className="py-3 pr-3">{row.programme_sem_label}</td>
                          <td className="py-3 pr-5">{row.hall_label}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="px-5 py-10 text-center text-sm text-[#9ca3af]">
                  No timetable entries yet. Regenerate to build from confirmed registrations.
                </p>
              )}
              <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
                <span>{data.papers_count_label}</span>
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
                ) : (
                  <span>{data.showing_label}</span>
                )}
              </div>
            </section>

          </>
        ) : null}
      </QueryState>
    </div>
  );
}