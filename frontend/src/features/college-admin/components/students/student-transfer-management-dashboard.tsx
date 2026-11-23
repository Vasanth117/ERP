"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { toast } from "sonner";

import { PlusIcon } from "@/components/icons/erp/generated/plus";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useSaveStudentTransferReview,
  useStudentTransferManagementPage,
} from "@/features/college-admin/hooks/use-student-transfer-management";
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


function ApprovalTimeline({
  steps,
  title,
}: {
  title: string;
  steps: { key: string; label: string; status_label: string; tone: string }[];
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
              <span
                className="absolute left-[5px] top-3 h-[calc(100%-4px)] w-px bg-[#e5e7eb]"
                aria-hidden
              />
            ) : null}
            <span
              className={cn(
                "relative z-[1] mt-1 size-2.5 shrink-0 rounded-full ring-4 ring-white",
                step.tone === "success"
                  ? "bg-[#10b981]"
                  : step.tone === "warning"
                    ? "bg-[#f97316]"
                    : step.tone === "info"
                      ? "bg-[#3b82f6]"
                      : "bg-[#d1d5db]",
              )}
            />
            <div>
              <p className="text-[13px] font-medium text-[#111827]">{step.label}</p>
              <p className="text-[12px] text-[#6b7280]">{step.status_label}</p>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}

export function StudentTransferManagementDashboard() {
  const [page, setPage] = useState(1);
  const [selectedKey, setSelectedKey] = useState<string | undefined>();
  const [transferType, setTransferType] = useState("");
  const [effectiveSemester, setEffectiveSemester] = useState("");
  const [reason, setReason] = useState("");

  const { data, isLoading, isError, error, refetch } = useStudentTransferManagementPage({
    page,
    selected_request_key: selectedKey,
  });

  const saveReview = useSaveStudentTransferReview();

  useEffect(() => {
    if (data?.selected_request_key && selectedKey !== data.selected_request_key) {
      setSelectedKey(data.selected_request_key);
    }
  }, [data?.selected_request_key, selectedKey]);

  useEffect(() => {
    if (!data) return;
    setTransferType(data.review_transfer_type);
    setEffectiveSemester(data.review_effective_semester);
    setReason(data.review_reason);
  }, [data?.selected_request_key, data?.review_transfer_type, data?.review_effective_semester, data?.review_reason, data]);

  const submitReview = (approveCollege: boolean) => {
    if (!selectedKey) {
      toast.error("Select a transfer request to review.");
      return;
    }
    saveReview.mutate(
      {
        request_key: selectedKey,
        transfer_type: transferType || undefined,
        effective_semester: effectiveSemester || undefined,
        reason,
        approve_college: approveCollege,
        page,
      },
      {
        onSuccess: (res) => {
          toast.success(approveCollege ? "College approval recorded." : "Review saved.");
          if (res.selected_request_key) setSelectedKey(res.selected_request_key);
        },
        onError: (e: Error) => toast.error(e.message),
      },
    );
  };

  return (
    <div className="space-y-5" data-figma-frame="158:5236">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Student Transfer Management"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">
            {data?.page_subtitle ?? "Programme, section and college transfers"}
          </p>
        </div>
        <Link
          href={data?.new_transfer_href ?? "/college-admin/students/all-students-list"}
          className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
        >
          <PlusIcon className="size-3.5" aria-hidden />
          {data?.new_transfer_label ?? "New transfer"}
        </Link>
      </div>

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.requests_section_title}</h3>
              </div>
              {data.transfer_rows.length ? (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[48rem] text-left text-[13px]">
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
                      {data.transfer_rows.map((row) => {
                        const selected = row.request_key === selectedKey;
                        return (
                          <tr
                            key={row.request_key}
                            className={cn(
                              "cursor-pointer text-[#374151] transition-colors",
                              selected ? "bg-[#eff6ff]" : "hover:bg-[#f9fafb]",
                            )}
                            onClick={() => setSelectedKey(row.request_key)}
                          >
                            <td className="px-5 py-3 font-mono text-[12px] text-[#6b7280]">{row.request_number}</td>
                            <td className="py-3 pr-3 font-medium text-[#111827]">{row.student_name}</td>
                            <td className="py-3 pr-3">{row.from_label}</td>
                            <td className="py-3 pr-3">{row.to_label}</td>
                            <td className="py-3 pr-3">{row.type_label}</td>
                            <td className="py-3 pr-5">
                              <StatusPill label={row.status_label} tone={row.status_tone} />
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="px-5 py-8 text-sm text-[#9ca3af]">No transfer requests yet.</p>
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

            {selectedKey ? (
              <div className="grid grid-cols-1 gap-5 lg:grid-cols-[1fr_280px]">
                <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                  <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                    <h3 className="text-[14px] font-semibold text-[#111827]">{data.review_section_title}</h3>
                  </div>
                  <div className="space-y-4 px-5 py-5">
                    <div>
                      <Label className="text-[12px] text-[#374151]">{data.review_student_field_label}</Label>
                      <input
                        readOnly
                        className="mt-1.5 h-9 w-full rounded-md border border-[#dce3ec] bg-[#f9fafb] px-3 text-[13px]"
                        value={data.review_student_line}
                      />
                    </div>
                    <div>
                      <Label className="text-[12px] text-[#374151]">{data.review_transfer_type_field_label}</Label>
                      <select
                        className="mt-1.5 h-9 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px]"
                        value={transferType}
                        onChange={(e) => setTransferType(e.target.value)}
                      >
                        {data.review_transfer_type_options.map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <Label className="text-[12px] text-[#374151]">{data.review_effective_field_label}</Label>
                      <select
                        className="mt-1.5 h-9 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px]"
                        value={effectiveSemester}
                        onChange={(e) => setEffectiveSemester(e.target.value)}
                      >
                        {data.review_effective_options
                          .filter((o) => o.value)
                          .map((opt) => (
                            <option key={opt.value} value={opt.value}>
                              {opt.label}
                            </option>
                          ))}
                      </select>
                    </div>
                    <div>
                      <Label className="text-[12px] text-[#374151]">{data.review_reason_field_label}</Label>
                      <textarea
                        className="mt-1.5 min-h-[88px] w-full rounded-md border border-[#dce3ec] bg-white px-3 py-2 text-[13px]"
                        value={reason}
                        onChange={(e) => setReason(e.target.value)}
                      />
                    </div>
                    <div className="flex flex-wrap gap-2 pt-1">
                      <Button
                        type="button"
                        variant="outline"
                        className="h-9 text-xs"
                        disabled={saveReview.isPending}
                        onClick={() => submitReview(false)}
                      >
                        {data.save_review_label}
                      </Button>
                      <Button
                        type="button"
                        className="h-9 bg-[#245dd8] text-xs hover:bg-[#1f4fb8]"
                        disabled={saveReview.isPending}
                        onClick={() => submitReview(true)}
                      >
                        {data.approve_college_label}
                      </Button>
                    </div>
                  </div>
                </section>

                <ApprovalTimeline steps={data.approval_steps} title={data.approval_route_title} />
              </div>
            ) : null}

          </>
        ) : null}
      </QueryState>
    </div>
  );
}