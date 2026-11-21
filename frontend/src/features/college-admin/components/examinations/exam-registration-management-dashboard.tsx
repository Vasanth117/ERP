"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";

import { CheckIcon } from "@/components/icons/erp/generated/check";
import { FilterIcon } from "@/components/icons/erp/generated/filter";
import { Button } from "@/components/ui/button";
import { CollegeAdminDownload } from "@/features/college-admin/components/layout/college-admin-erp-icons";
import {
  CollegeAdminKpiGrid,
  CollegeAdminUserDashboardKpiCard,
} from "@/features/college-admin/components/ui/college-admin-kpi-card";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useConfirmSelectedExamRegistrations,
  useExamRegistrationManagementPage,
} from "@/features/college-admin/hooks/use-exam-registration-management";
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
          "h-9 min-w-[9rem] max-w-[18rem] rounded-md border border-[#dce3ec] bg-white pr-8 text-[13px] text-[#374151]",
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

function formatSnapshot(iso: string) {
  try {
    return new Intl.DateTimeFormat("en-IN", {
      dateStyle: "medium",
      timeStyle: "short",
      timeZone: "Asia/Kolkata",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

export function ExamRegistrationManagementDashboard() {
  const [page, setPage] = useState(1);
  const [sessionId, setSessionId] = useState("");
  const [status, setStatus] = useState("");
  const [programme, setProgramme] = useState("");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    setPage(1);
    setSelectedIds(new Set());
  }, [sessionId, status, programme]);

  const { data, isLoading, isError, error, refetch } = useExamRegistrationManagementPage({
    page,
    session_id: sessionId || undefined,
    status: status || undefined,
    programme_code: programme || undefined,
  });

  const confirmMutation = useConfirmSelectedExamRegistrations();

  useEffect(() => {
    if (data?.selected_session_id && !sessionId) {
      setSessionId(data.selected_session_id);
    }
  }, [data?.selected_session_id, sessionId]);

  const handleExport = useCallback(() => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `exam-registration-${new Date(data.generated_at).toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data]);

  const toggleRow = (registrationId: string, checked: boolean) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (checked) next.add(registrationId);
      else next.delete(registrationId);
      return next;
    });
  };

  const handleConfirmSelected = () => {
    if (!data?.selected_session_id) return;
    if (!selectedIds.size) {
      toast.error("Select at least one submitted registration with cleared fees.");
      return;
    }
    confirmMutation.mutate(
      {
        registration_ids: [...selectedIds],
        session_id: data.selected_session_id,
        status: status || undefined,
        programme_code: programme || undefined,
        page,
      },
      {
        onSuccess: () => {
          toast.success("Selected registrations confirmed.");
          setSelectedIds(new Set());
        },
        onError: (e: Error) => toast.error(e.message),
      },
    );
  };

  return (
    <div className="space-y-5" data-figma-frame="159:12120">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Exam Registration Management"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">
            {data?.page_subtitle ?? "Review and confirm student exam registrations"}
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <Button
            type="button"
            variant="outline"
            className="h-9 gap-1.5 border-[#dce3ec] text-xs font-medium text-[#374151]"
            onClick={handleExport}
            disabled={isLoading || !data}
          >
            <CollegeAdminDownload className="size-3.5" />
            {data?.export_label ?? "Export"}
          </Button>
          <Button
            type="button"
            className="h-9 gap-1.5 bg-[#245dd8] text-xs font-medium text-white hover:bg-[#1f4fb8]"
            onClick={handleConfirmSelected}
            disabled={isLoading || confirmMutation.isPending || !selectedIds.size}
          >
            <CheckIcon className="size-3.5" aria-hidden />
            {data?.confirm_selected_label ?? "Confirm selected"}
          </Button>
        </div>
      </div>

      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-wrap items-center gap-2">
          <FilterSelect
            label={data?.session_filter_label ?? "Exam session"}
            value={sessionId}
            onChange={setSessionId}
            options={
              data?.session_options?.length
                ? data.session_options
                : [{ value: "", label: "Exam session" }]
            }
          />
          <FilterSelect
            icon={<FilterIcon className="size-3.5" aria-hidden />}
            label={data?.status_filter_label ?? "Status"}
            value={status}
            onChange={setStatus}
            options={data?.status_options ?? [{ value: "", label: "All statuses" }]}
          />
          <FilterSelect
            icon={<FilterIcon className="size-3.5" aria-hidden />}
            label={data?.programme_filter_label ?? "Programme"}
            value={programme}
            onChange={setProgramme}
            options={data?.programme_options ?? [{ value: "", label: "All programmes" }]}
          />
        </div>
        <div className="flex flex-wrap items-center gap-3 text-[12px] text-[#6b7280]">
          <span className="inline-flex items-center gap-1.5 rounded-full border border-[#e8ecf2] bg-white px-2.5 py-1">
            <span className="size-1.5 rounded-full bg-[#245dd8]" />
            {data?.scope_indicator_label ?? "College scope"}
          </span>
          <span className="tabular-nums">{data?.updated_at_label ?? "—"}</span>
        </div>
      </div>

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <h3 className="text-[14px] font-semibold text-[#111827]">{data.registration_window_title}</h3>
                  <p className="mt-1 text-[13px] text-[#6b7280]">{data.registration_window_open_label}</p>
                  <p className="text-[13px] text-[#6b7280]">{data.registration_window_close_label}</p>
                </div>
                <StatusPill
                  label={data.registration_window_status_label}
                  tone={data.registration_window_status_tone}
                />
              </div>
            </section>

            <CollegeAdminKpiGrid>
              {data.kpis.map((kpi, index) => (
                <CollegeAdminUserDashboardKpiCard key={kpi.key} kpi={kpi} index={index} />
              ))}
            </CollegeAdminKpiGrid>

            <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="flex items-center justify-between border-b border-[#f1f5f9] px-5 py-3.5">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.registrations_section_title}</h3>
                <span className="text-[12px] text-[#6b7280]">{data.registration_count_label}</span>
              </div>
              {data.registration_rows.length ? (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[48rem] text-left text-[13px]">
                    <thead>
                      <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                        <th className="w-10 px-5 pb-3 font-medium" aria-label="Select" />
                        {data.table_headers.map((header, index) => (
                          <th
                            key={header}
                            className={cn(
                              "pb-3 font-medium",
                              index === 0 ? "pl-0" : "pr-3",
                              index === data.table_headers.length - 1 ? "pr-5" : "",
                            )}
                          >
                            {header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#f1f5f9]">
                      {data.registration_rows.map((row) => (
                        <tr key={row.registration_id} className="text-[#374151]">
                          <td className="px-5 py-3">
                            <input
                              type="checkbox"
                              className="size-4 rounded border-[#dce3ec]"
                              disabled={!row.is_selectable}
                              checked={selectedIds.has(row.registration_id)}
                              onChange={(e) => toggleRow(row.registration_id, e.target.checked)}
                              aria-label={`Select ${row.student_name}`}
                            />
                          </td>
                          <td className="py-3 pr-3 font-medium text-[#111827]">
                            <Link href={row.detail_href} className="hover:text-[#245dd8]">
                              {row.student_name}
                            </Link>
                          </td>
                          <td className="py-3 pr-3 font-mono text-[12px] text-[#6b7280]">{row.register_number}</td>
                          <td className="py-3 pr-3">{row.programme_label}</td>
                          <td className="py-3 pr-3 tabular-nums">{row.subjects_count}</td>
                          <td className="py-3 pr-3">
                            <StatusPill label={row.fee_status_label} tone={row.fee_status_tone} />
                          </td>
                          <td className="py-3 pr-3">
                            <StatusPill label={row.registration_status_label} tone={row.registration_status_tone} />
                          </td>
                          <td className="py-3 pr-5 text-[12px] text-[#6b7280]">{row.submitted_at_label}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="px-5 py-8 text-sm text-[#9ca3af]">No registrations match your filters.</p>
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