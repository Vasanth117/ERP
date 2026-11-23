"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

import { CalendarIcon } from "@/components/icons/erp/generated/calendar";
import { CheckIcon } from "@/components/icons/erp/generated/check";
import { SendIcon } from "@/components/icons/erp/generated/send";
import { XIcon } from "@/components/icons/erp/generated/x";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useCancelStudentWithdrawalDraft,
  useStudentWithdrawalDiscontinuationPage,
  useSubmitStudentWithdrawal,
} from "@/features/college-admin/hooks/use-student-withdrawal-discontinuation";
import { cn } from "@/lib/utils";

function WizardStepper({
  steps,
  activeKey,
  activeIndex,
}: {
  steps: { key: string; label: string; step_number: number }[];
  activeKey: string;
  activeIndex: number;
}) {
  return (
    <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white px-4 py-4 shadow-[0_1px_2px_rgba(15,23,42,0.04)] sm:px-8">
      <div className="flex items-center">
        {steps.map((wizardStep, index) => {
          const active = wizardStep.key === activeKey;
          const done = index < activeIndex;
          return (
            <div key={wizardStep.key} className="flex min-w-0 flex-1 items-center last:flex-none">
              <div className="flex min-w-0 items-center gap-2.5">
                <span
                  className={cn(
                    "flex size-8 shrink-0 items-center justify-center rounded-full text-[13px] font-semibold tabular-nums",
                    active && "border-2 border-[#245dd8] bg-white text-[#245dd8]",
                    !active && !done && "border border-[#e5e7eb] bg-[#f9fafb] text-[#9ca3af]",
                    done && !active && "border-2 border-[#245dd8] bg-[#245dd8] text-white",
                  )}
                >
                  {done ? <CheckIcon className="size-3.5" strokeWidth={2.5} aria-hidden /> : wizardStep.step_number}
                </span>
                <span
                  className={cn(
                    "truncate text-[13px] sm:text-[14px]",
                    active || done ? "font-semibold text-[#111827]" : "font-medium text-[#9ca3af]",
                  )}
                >
                  {wizardStep.label}
                </span>
              </div>
              {index < steps.length - 1 ? (
                <div
                  className={cn(
                    "mx-3 hidden h-px min-w-[1.5rem] flex-1 sm:block",
                    index < activeIndex ? "bg-[#245dd8]" : "bg-[#e5e7eb]",
                  )}
                  aria-hidden
                />
              ) : null}
            </div>
          );
        })}
      </div>
    </section>
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

function RequiredLabel({ children }: { children: React.ReactNode }) {
  return (
    <Label className="text-[12px] text-[#374151]">
      {children}
      <span className="text-[#dc2626]"> *</span>
    </Label>
  );
}


function ProcessTimeline({
  title,
  steps,
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

export function StudentWithdrawalDiscontinuationDashboard() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const recordId = searchParams.get("record_id") ?? undefined;
  const requestId = searchParams.get("request_id") ?? undefined;

  const query = useMemo(
    () => ({ record_id: recordId, request_id: requestId }),
    [recordId, requestId],
  );

  const { data, isLoading, isError, error, refetch } = useStudentWithdrawalDiscontinuationPage(query);
  const submitMutation = useSubmitStudentWithdrawal();
  const cancelMutation = useCancelStudentWithdrawalDraft();

  const [withdrawalType, setWithdrawalType] = useState("");
  const [lastAttendance, setLastAttendance] = useState("");
  const [reason, setReason] = useState("");

  useEffect(() => {
    if (!data) return;
    setWithdrawalType(data.withdrawal_type);
    setLastAttendance(data.last_attendance_date);
    setReason(data.reason);
  }, [data?.request_id, data?.withdrawal_type, data?.last_attendance_date, data?.reason, data]);

  const handleCancel = async () => {
    const href = data?.cancel_href ?? "/college-admin/students/student-status-management";
    if (data?.request_id && data.can_submit) {
      try {
        await cancelMutation.mutateAsync(data.request_id);
      } catch (e) {
        toast.error(e instanceof Error ? e.message : "Could not cancel draft.");
        return;
      }
    }
    router.push(href);
  };

  const handleSubmit = () => {
    if (!data?.selected_record_id) {
      toast.error("Select a student from Status management first.");
      return;
    }
    if (!reason.trim()) {
      toast.error("Reason is required.");
      return;
    }
    submitMutation.mutate(
      {
        record_id: data.selected_record_id,
        request_id: data.request_id,
        withdrawal_type: withdrawalType,
        last_attendance_date: lastAttendance || null,
        reason: reason.trim(),
      },
      {
        onSuccess: () => toast.success("Withdrawal request submitted for approval."),
        onError: (e: Error) => toast.error(e.message),
      },
    );
  };

  const readOnly = Boolean(data?.selected_record_id && !data.can_submit);

  return (
    <div className="space-y-5" data-figma-frame="158:6620">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Student Withdrawal / Discontinuation"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">{data?.page_subtitle ?? "Controlled exit workflow"}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            type="button"
            variant="outline"
            className="h-9 gap-1.5 border-[#dce3ec] text-xs text-[#374151]"
            onClick={() => void handleCancel()}
          >
            <XIcon className="size-3.5" aria-hidden />
            {data?.cancel_label ?? "Cancel"}
          </Button>
          <Button
            type="button"
            className="h-9 gap-1.5 bg-[#245dd8] text-xs hover:bg-[#1f4fb8]"
            disabled={!data?.can_submit || submitMutation.isPending}
            onClick={handleSubmit}
          >
            <SendIcon className="size-3.5" aria-hidden />
            {data?.submit_for_approval_label ?? "Submit for approval"}
          </Button>
        </div>
      </div>

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            {!data.selected_record_id ? (
              <div className="rounded-xl border border-dashed border-[#dce3ec] bg-[#f9fafb] px-5 py-10 text-center text-sm text-[#6b7280]">
                <p>Choose a student on the Status page, then use Change status to open this workflow.</p>
                <Link
                  href={data.cancel_href}
                  className="mt-3 inline-flex text-[#245dd8] underline-offset-2 hover:underline"
                >
                  Back to Status management
                </Link>
              </div>
            ) : (
              <>
                <WizardStepper
                  steps={data.wizard_steps}
                  activeKey={data.active_step_key}
                  activeIndex={data.active_step_index}
                />

                <div className="grid grid-cols-1 gap-5 lg:grid-cols-[1fr_280px]">
                  <div className="space-y-5">
                    <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                      <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                        <h3 className="text-[14px] font-semibold text-[#111827]">
                          {data.withdrawal_request_section_title}
                        </h3>
                      </div>
                      <div className="grid gap-4 px-5 py-5 sm:grid-cols-2">
                        <div className="sm:col-span-2">
                          <RequiredLabel>{data.student_field_label}</RequiredLabel>
                          <input
                            readOnly
                            className="mt-1.5 h-9 w-full rounded-md border border-[#dce3ec] bg-[#f9fafb] px-3 text-[13px]"
                            value={data.student_line}
                          />
                        </div>
                        <div>
                          <RequiredLabel>{data.type_field_label}</RequiredLabel>
                          <select
                            className="mt-1.5 h-9 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px] disabled:bg-[#f9fafb]"
                            value={withdrawalType}
                            disabled={readOnly}
                            onChange={(e) => setWithdrawalType(e.target.value)}
                          >
                            {data.withdrawal_type_options.map((opt) => (
                              <option key={opt.value} value={opt.value}>
                                {opt.label}
                              </option>
                            ))}
                          </select>
                        </div>
                        <div>
                          <Label className="text-[12px] text-[#374151]">{data.last_attendance_field_label}</Label>
                          <div className="relative mt-1.5">
                            <CalendarIcon
                              className="pointer-events-none absolute left-3 top-1/2 size-3.5 -translate-y-1/2 text-[#9ca3af]"
                              aria-hidden
                            />
                            <input
                              type="date"
                              className="h-9 w-full rounded-md border border-[#dce3ec] bg-white pl-9 pr-3 text-[13px] disabled:bg-[#f9fafb]"
                              value={lastAttendance}
                              disabled={readOnly}
                              onChange={(e) => setLastAttendance(e.target.value)}
                            />
                          </div>
                        </div>
                        <div className="sm:col-span-2">
                          <RequiredLabel>{data.reason_field_label}</RequiredLabel>
                          <textarea
                            className="mt-1.5 min-h-[88px] w-full resize-y rounded-md border border-[#dce3ec] bg-white px-3 py-2 text-[13px] disabled:bg-[#f9fafb]"
                            value={reason}
                            disabled={readOnly}
                            maxLength={500}
                            onChange={(e) => setReason(e.target.value)}
                          />
                        </div>
                      </div>
                    </section>

                    <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                      <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                        <h3 className="text-[14px] font-semibold text-[#111827]">{data.clearances_section_title}</h3>
                      </div>
                      {data.clearance_rows.length ? (
                        <div className="overflow-x-auto">
                          <table className="w-full text-left text-[13px]">
                            <thead>
                              <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                                {data.clearance_table_headers.map((header, index) => (
                                  <th
                                    key={header}
                                    className={cn("pb-3 font-medium", index === 0 ? "px-5" : "pr-3", "last:pr-5")}
                                  >
                                    {header}
                                  </th>
                                ))}
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-[#f1f5f9]">
                              {data.clearance_rows.map((row) => (
                                <tr key={row.department_key} className="text-[#374151]">
                                  <td className="px-5 py-3 font-medium text-[#111827]">{row.department_label}</td>
                                  <td className="py-3 pr-3">
                                    <StatusPill label={row.status_label} tone={row.status_tone} />
                                  </td>
                                  <td className="py-3 pr-5 text-[#6b7280]">{row.cleared_on_label}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      ) : null}
                      <div className="border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
                        {data.clearances_summary_label}
                      </div>
                    </section>
                  </div>

                  <ProcessTimeline title={data.process_section_title} steps={data.process_steps} />
                </div>

              </>
            )}
          </>
        ) : null}
      </QueryState>
    </div>
  );
}