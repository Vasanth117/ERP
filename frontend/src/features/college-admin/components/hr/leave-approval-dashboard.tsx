"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

import { CheckIcon } from "@/components/icons/erp/generated/check";
import { ChevronLeftIcon } from "@/components/icons/erp/generated/chevron-left";
import { XIcon } from "@/components/icons/erp/generated/x";
import { Button, buttonVariants } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { onCollegeAdminMutationError } from "@/features/college-admin/context/college-admin-validation-context";
import { useDecideHrLeave, useHrLeaveApprovalPage } from "@/features/college-admin/hooks/use-hr-attendance-leave";
import { cn } from "@/lib/utils";

function ApprovalTimeline({
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
        {steps.length ? (
          steps.map((step, index) => (
            <li key={step.key} className="relative flex gap-3 pb-5 last:pb-0">
              {index < steps.length - 1 ? (
                <span className="absolute left-[5px] top-3 h-[calc(100%-4px)] w-px bg-[#e5e7eb]" aria-hidden />
              ) : null}
              <span
                className={cn(
                  "relative z-[1] mt-1 size-2.5 shrink-0 rounded-full ring-4 ring-white",
                  step.tone === "success"
                    ? "bg-[#10b981]"
                    : step.tone === "warning"
                      ? "bg-[#f97316]"
                      : step.tone === "error"
                        ? "bg-[#ef4444]"
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
          ))
        ) : (
          <li className="py-2 text-[13px] text-[#9ca3af]">No timeline steps yet.</li>
        )}
      </ol>
    </section>
  );
}

export function LeaveApprovalDashboard() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const leaveIdParam = useMemo(() => searchParams.get("id") ?? undefined, [searchParams]);

  const { data, isLoading, isError, error, refetch } = useHrLeaveApprovalPage(leaveIdParam);
  const activeLeaveId = leaveIdParam ?? data?.selected_leave_request_id ?? undefined;
  const decide = useDecideHrLeave(activeLeaveId);

  const [decision, setDecision] = useState("");
  const [remarks, setRemarks] = useState("");

  useEffect(() => {
    if (data?.selected_decision) setDecision(data.selected_decision);
    if (data?.remarks_value !== undefined) setRemarks(data.remarks_value);
  }, [data?.selected_decision, data?.remarks_value, activeLeaveId]);

  const submitDecision = (approved: boolean) => {
    if (!activeLeaveId || !data?.can_decide) {
      toast.error(data?.decide_blocked_message ?? "Cannot submit decision for this application");
      return;
    }
    const finalDecision = approved ? "approved" : "rejected";
    decide.mutate(
      {
        leave_request_id: activeLeaveId,
        decision: finalDecision,
        note: remarks || undefined,
      },
      {
        onSuccess: () => {
          toast.success(approved ? "Leave approved" : "Leave rejected");
          router.push(data.return_href);
        },
        onError: onCollegeAdminMutationError,
      },
    );
  };

  return (
    <div className="space-y-5" data-figma-frame="160:9168">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Link
              href={data?.back_href ?? "/college-admin/hr/leave-management"}
              className="inline-flex items-center text-[#6b7280] hover:text-[#111827]"
              aria-label={data?.back_label ?? "Back"}
            >
              <ChevronLeftIcon className="size-5" aria-hidden />
            </Link>
            <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
              {data?.page_title ?? "Leave Approval"}
            </h2>
          </div>
          <p className="text-[14px] text-[#6b7280]">{data?.page_subtitle ?? "Review leave application"}</p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <Link
            href={data?.return_href ?? "/college-admin/hr/leave-management"}
            className={cn(buttonVariants({ variant: "outline" }), "h-9 gap-1.5 text-xs")}
          >
            <ChevronLeftIcon className="size-3.5" aria-hidden />
            {data?.return_label ?? "Return"}
          </Link>
          <Button
            type="button"
            variant="outline"
            className="h-9 gap-1.5 text-xs"
            disabled={!data?.can_decide || decide.isPending}
            onClick={() => submitDecision(false)}
          >
            <XIcon className="size-3.5" aria-hidden />
            {data?.reject_label ?? "Reject"}
          </Button>
          <Button
            type="button"
            className="h-9 gap-1.5 bg-[#245dd8] text-xs text-white hover:bg-[#1f4fb8]"
            disabled={!data?.can_decide || decide.isPending}
            onClick={() => submitDecision(true)}
          >
            <CheckIcon className="size-3.5" aria-hidden />
            {data?.approve_label ?? "Approve"}
          </Button>
        </div>
      </div>

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            {data.decide_blocked_message ? (
              <p className="rounded-lg border border-[#fef3c7] bg-[#fffbeb] px-4 py-3 text-[13px] text-[#92400e]">
                {data.decide_blocked_message}
              </p>
            ) : null}

            <div className="grid gap-5 lg:grid-cols-[1fr_minmax(260px,320px)]">
              <div className="space-y-5">
                <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                  <h3 className="mb-4 text-[14px] font-semibold text-[#111827]">{data.application_card_title}</h3>
                  <dl className="grid gap-4 sm:grid-cols-2">
                    <div>
                      <dt className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                        {data.employee_field_label}
                      </dt>
                      <dd className="mt-1 text-[14px] font-semibold text-[#111827]">{data.employee_label}</dd>
                    </div>
                    <div>
                      <dt className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                        {data.leave_type_field_label}
                      </dt>
                      <dd className="mt-1 text-[14px] font-semibold text-[#111827]">{data.leave_type_label}</dd>
                    </div>
                    <div>
                      <dt className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                        {data.dates_field_label}
                      </dt>
                      <dd className="mt-1 text-[14px] font-semibold text-[#111827]">{data.dates_label}</dd>
                    </div>
                    <div>
                      <dt className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                        {data.balance_after_field_label}
                      </dt>
                      <dd className="mt-1 text-[14px] font-semibold text-[#111827]">{data.balance_after_label}</dd>
                    </div>
                    <div className="sm:col-span-2">
                      <dt className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                        {data.cover_field_label}
                      </dt>
                      <dd className="mt-1 text-[14px] font-semibold text-[#111827]">{data.cover_label}</dd>
                    </div>
                  </dl>
                </section>

                <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                  <h3 className="mb-4 text-[14px] font-semibold text-[#111827]">{data.decision_card_title}</h3>
                  <div className="space-y-4">
                    <div className="space-y-1.5">
                      <Label className="text-[13px] text-[#374151]">
                        {data.decision_field_label}
                        {data.decision_required ? <span className="text-[#dc2626]"> *</span> : null}
                      </Label>
                      <select
                        value={decision}
                        onChange={(e) => setDecision(e.target.value)}
                        className="h-9 w-full rounded-md border border-[#e5e7eb] bg-white px-3 text-[13px] text-[#111827]"
                        disabled={!data.can_decide}
                      >
                        {data.decision_options.map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="space-y-1.5">
                      <Label className="text-[13px] text-[#374151]">{data.remarks_field_label}</Label>
                      <textarea
                        value={remarks}
                        onChange={(e) => setRemarks(e.target.value)}
                        placeholder={data.remarks_placeholder}
                        rows={4}
                        disabled={!data.can_decide}
                        className="w-full rounded-md border border-[#e5e7eb] bg-white px-3 py-2 text-[13px] text-[#111827] placeholder:text-[#9ca3af]"
                      />
                    </div>
                  </div>
                </section>
              </div>

              <ApprovalTimeline title={data.approval_timeline_title} steps={data.approval_steps} />
            </div>
          </>
        ) : null}
      </QueryState>
    </div>
  );
}