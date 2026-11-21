"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { toast } from "sonner";

import { ArrowRightLeftIcon } from "@/components/icons/erp/generated/arrow-right-left";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useApproveEmployeeStatusChange,
  useEmployeeStatusManagementPage,
  useSubmitEmployeeStatusChange,
} from "@/features/college-admin/hooks/use-employee-status-management";
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

function mixBarColor(tone: string) {
  switch (tone) {
    case "success":
      return "bg-[#10b981]";
    case "warning":
      return "bg-[#d97706]";
    case "error":
      return "bg-[#ef4444]";
    case "info":
      return "bg-[#3b82f6]";
    default:
      return "bg-[#6b7280]";
  }
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

function RequiredLabel({ children }: { children: React.ReactNode }) {
  return (
    <Label className="text-[12px] text-[#374151]">
      {children}
      <span className="text-[#dc2626]"> *</span>
    </Label>
  );
}

export function EmployeeStatusManagementDashboard() {
  const [page, setPage] = useState(1);
  const [selectedRequestId, setSelectedRequestId] = useState<string | undefined>();
  const [recordId, setRecordId] = useState("");
  const [newStatus, setNewStatus] = useState("");
  const [reason, setReason] = useState("");
  const [effectiveDate, setEffectiveDate] = useState("");

  const { data, isLoading, isError, error, refetch } = useEmployeeStatusManagementPage({
    page,
    selected_request_id: selectedRequestId,
  });

  const submitChange = useSubmitEmployeeStatusChange();
  const approveChange = useApproveEmployeeStatusChange();

  useEffect(() => {
    if (data?.selected_request_id && selectedRequestId !== data.selected_request_id) {
      setSelectedRequestId(data.selected_request_id ?? undefined);
    }
  }, [data?.selected_request_id, selectedRequestId]);

  useEffect(() => {
    if (!data) return;
    setRecordId(data.form_record_id);
    setNewStatus(data.form_new_status);
    setReason(data.form_reason);
    setEffectiveDate(data.form_effective_date);
  }, [data?.selected_request_id, data?.form_record_id, data?.form_new_status, data?.form_reason, data?.form_effective_date, data]);

  const handleSubmit = () => {
    if (!recordId || !newStatus || !reason.trim()) {
      toast.error("Fill employee, new status, and reason.");
      return;
    }
    submitChange.mutate(
      {
        record_id: recordId,
        new_status: newStatus,
        reason: reason.trim(),
        effective_date: effectiveDate || undefined,
        page,
      },
      {
        onSuccess: (res) => {
          toast.success("Status change submitted for approval.");
          if (res.selected_request_id) setSelectedRequestId(res.selected_request_id);
        },
        onError: (e: Error) => toast.error(e.message),
      },
    );
  };

  const handleApprove = () => {
    if (!selectedRequestId) {
      toast.error("Select a pending status change to approve.");
      return;
    }
    const row = data?.status_change_rows.find((r) => r.request_id === selectedRequestId);
    if (row?.approval_status_label !== "Pending") {
      toast.error("Only pending changes can be approved.");
      return;
    }
    approveChange.mutate(
      { request_id: selectedRequestId, page },
      {
        onSuccess: () => toast.success("Status change approved and applied."),
        onError: (e: Error) => toast.error(e.message),
      },
    );
  };

  const selectedPending =
    data?.status_change_rows.find((r) => r.request_id === selectedRequestId)?.approval_status_label === "Pending";

  return (
    <div className="space-y-5" data-figma-frame="CA-07.12">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Employee Status Management"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">{data?.page_subtitle ?? "—"}</p>
        </div>
        <Link
          href={data?.change_status_href ?? "/college-admin/faculty/employee-status-management#update-status"}
          className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
        >
          <ArrowRightLeftIcon className="size-3.5" aria-hidden />
          {data?.change_status_label ?? "Change status"}
        </Link>
      </div>

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.status_changes_section_title}</h3>
              </div>
              {data.status_change_rows.length ? (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[52rem] text-left text-[13px]">
                    <thead>
                      <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                        {data.table_headers.map((header, index) => (
                          <th
                            key={header}
                            className={cn(
                              "pb-3 font-medium",
                              index === 0 ? "px-5" : "pr-3",
                              index === data.table_headers.length - 1 ? "pr-5" : "",
                            )}
                          >
                            {header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#f1f5f9]">
                      {data.status_change_rows.map((row) => {
                        const selected = row.request_id === selectedRequestId;
                        return (
                          <tr
                            key={row.request_id}
                            className={cn(
                              "cursor-pointer text-[#374151] transition-colors",
                              selected ? "bg-[#eff6ff]" : "hover:bg-[#f9fafb]",
                            )}
                            onClick={() => setSelectedRequestId(row.request_id)}
                          >
                            <td className="px-5 py-3 font-medium text-[#111827]">{row.employee_name}</td>
                            <td className="py-3 pr-3">{row.current_status_label}</td>
                            <td className="py-3 pr-3">{row.new_status_label}</td>
                            <td className="py-3 pr-3 tabular-nums text-[#6b7280]">{row.effective_label}</td>
                            <td className="max-w-[12rem] truncate py-3 pr-3" title={row.reason_label}>
                              {row.reason_label}
                            </td>
                            <td className="py-3 pr-5">
                              <StatusPill label={row.approval_status_label} tone={row.approval_status_tone} />
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="px-5 py-8 text-sm text-[#9ca3af]">No status changes recorded yet.</p>
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

            <div className="grid grid-cols-1 gap-5 lg:grid-cols-[1fr_320px]">
              <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                  <h3 className="text-[14px] font-semibold text-[#111827]">{data.status_mix_title}</h3>
                </div>
                <ul className="space-y-4 px-5 py-5">
                  {data.status_mix_items.map((item) => (
                    <li key={item.status_key}>
                      <div className="flex items-baseline justify-between gap-2 text-[13px]">
                        <span className="font-medium text-[#111827]">{item.status_label}</span>
                        <span className="tabular-nums text-[#374151]">{item.count.toLocaleString("en-IN")}</span>
                      </div>
                      <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-[#f3f4f6]">
                        <div
                          className={cn("h-full rounded-full transition-all", mixBarColor(item.tone))}
                          style={{ width: `${Math.min(100, Math.max(0, item.bar_percent))}%` }}
                        />
                      </div>
                    </li>
                  ))}
                </ul>
              </section>

              <section
                id="update-status"
                className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]"
              >
                <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                  <h3 className="text-[14px] font-semibold text-[#111827]">{data.update_status_section_title}</h3>
                </div>
                <div className="space-y-4 px-5 py-5">
                  <div>
                    <RequiredLabel>{data.employee_field_label}</RequiredLabel>
                    <select
                      className="mt-1.5 h-9 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px]"
                      value={recordId}
                      onChange={(e) => setRecordId(e.target.value)}
                    >
                      {!recordId ? <option value="">Select employee</option> : null}
                      {data.employee_picker_options.map((opt) => (
                        <option key={opt.record_id} value={opt.record_id}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <RequiredLabel>{data.new_status_field_label}</RequiredLabel>
                    <select
                      className="mt-1.5 h-9 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px]"
                      value={newStatus}
                      onChange={(e) => setNewStatus(e.target.value)}
                    >
                      {!newStatus ? <option value="">Select status</option> : null}
                      {data.new_status_options.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <Label className="text-[12px] text-[#374151]">{data.effective_date_field_label}</Label>
                    <input
                      type="date"
                      className="mt-1.5 h-9 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px]"
                      value={effectiveDate}
                      onChange={(e) => setEffectiveDate(e.target.value)}
                    />
                  </div>
                  <div>
                    <RequiredLabel>{data.reason_field_label}</RequiredLabel>
                    <textarea
                      className="mt-1.5 min-h-[88px] w-full resize-y rounded-md border border-[#dce3ec] bg-white px-3 py-2 text-[13px]"
                      value={reason}
                      onChange={(e) => setReason(e.target.value)}
                      maxLength={500}
                    />
                  </div>
                  <div className="flex flex-col gap-2 pt-1">
                    <Button
                      type="button"
                      className="h-9 w-full bg-[#245dd8] text-xs hover:bg-[#1f4fb8]"
                      disabled={submitChange.isPending}
                      onClick={handleSubmit}
                    >
                      {data.submit_status_label}
                    </Button>
                    {selectedPending ? (
                      <Button
                        type="button"
                        variant="outline"
                        className="h-9 w-full border-[#10b981] text-xs text-[#047857] hover:bg-[#ecfdf5]"
                        disabled={approveChange.isPending}
                        onClick={handleApprove}
                      >
                        {data.approve_status_label}
                      </Button>
                    ) : null}
                  </div>
                </div>
              </section>
            </div>

            <footer className="flex flex-wrap items-center justify-between gap-2 text-[11px] text-[#9ca3af]">
              <span>{data.footer_disclaimer}</span>
              <span>
                {data.footer_snapshot_label} · {formatSnapshot(data.generated_at)}
              </span>
            </footer>
          </>
        ) : null}
      </QueryState>
    </div>
  );
}