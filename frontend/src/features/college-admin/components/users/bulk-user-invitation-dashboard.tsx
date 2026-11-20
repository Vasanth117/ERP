"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useMemo, useRef, useState } from "react";
import { toast } from "sonner";

import { CheckIcon } from "@/components/icons/erp/generated/check";
import { ChevronLeftIcon } from "@/components/icons/erp/generated/chevron-left";
import { CollegeAdminDownload } from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { SendHorizontalIcon } from "@/components/icons/erp/generated/send-horizontal";
import { UploadIcon } from "@/components/icons/erp/generated/upload";
import { XIcon } from "@/components/icons/erp/generated/x";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useBulkUserInvitationPage,
  useBulkUserInvitationSettings,
  useSendBulkUserInvitations,
  useUploadBulkUserInvitation,
} from "@/features/college-admin/hooks/use-bulk-user-invitation";
import { downloadBulkInviteTemplate } from "@/features/college-admin/api/users";
import type { BulkUserInvitationPreviewRow, BulkUserInvitationSummaryStat } from "@/features/college-admin/types/bulk-user-invitation";
import { cn } from "@/lib/utils";

const DEFAULT_STEPS = [
  { key: "upload", label: "Upload file", step_number: 1 },
  { key: "map_validate", label: "Map & validate", step_number: 2 },
  { key: "preview", label: "Preview", step_number: 3 },
  { key: "send_invites", label: "Send invites", step_number: 4 },
] as const;

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

function StatusPill({ row }: { row: BulkUserInvitationPreviewRow }) {
  const styles: Record<string, string> = {
    success: "bg-[#ecfdf5] text-[#047857]",
    error: "bg-[#fef2f2] text-[#b91c1c]",
    warning: "bg-[#fff7ed] text-[#c2410c]",
    muted: "bg-[#f3f4f6] text-[#6b7280]",
  };
  const dot: Record<string, string> = {
    success: "bg-[#10b981]",
    error: "bg-[#ef4444]",
    warning: "bg-[#f97316]",
    muted: "bg-[#9ca3af]",
  };
  const key = row.status_tone in styles ? row.status_tone : "muted";
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[11px] font-medium", styles[key])}>
      <span className={cn("size-1.5 rounded-full", dot[key])} />
      {row.status_label}
    </span>
  );
}

function SummaryCard({ stat }: { stat: BulkUserInvitationSummaryStat }) {
  const border: Record<string, string> = {
    success: "border-[#a7f3d0] bg-[#ecfdf5]",
    error: "border-[#fecaca] bg-[#fef2f2]",
    warning: "border-[#fed7aa] bg-[#fff7ed]",
  };
  const key = stat.tone in border ? stat.tone : "muted";
  return (
    <div className={cn("rounded-lg border px-3 py-2.5", border[key] ?? "border-[#e5e7eb] bg-[#f9fafb]")}>
      <p className="text-[11px] font-medium text-[#6b7280]">{stat.label}</p>
      <p className="text-xl font-bold tabular-nums text-[#111827]">{stat.count}</p>
      <p className="text-[10px] text-[#6b7280]">{stat.description}</p>
    </div>
  );
}

export function BulkUserInvitationDashboard() {
  const router = useRouter();
  const fileRef = useRef<HTMLInputElement>(null);
  const [page, setPage] = useState(1);
  const [skipErrors, setSkipErrors] = useState(true);
  const [requireMfa, setRequireMfa] = useState(true);

  const pageQuery = useBulkUserInvitationPage(page);
  const upload = useUploadBulkUserInvitation();
  const settings = useBulkUserInvitationSettings();
  const send = useSendBulkUserInvitations();

  const data = pageQuery.data;

  useEffect(() => {
    if (!data) return;
    const skip = data.invitation_toggles.find((t) => t.key === "skip_rows_with_errors");
    const mfa = data.invitation_toggles.find((t) => t.key === "require_mfa_first_login");
    if (skip) setSkipErrors(skip.default_on);
    if (mfa) setRequireMfa(mfa.default_on);
  }, [data]);

  const activeStep = data?.current_step_key ?? "upload";
  const stepIndex = useMemo(() => {
    const steps = data?.steps ?? DEFAULT_STEPS;
    const idx = steps.findIndex((s) => s.key === activeStep);
    if (idx >= 0) return idx;
    if (data?.preview_rows.length) return 2;
    return 0;
  }, [activeStep, data?.preview_rows.length, data?.steps]);

  const onFile = useCallback(
    async (file: File) => {
      if (!file.name.toLowerCase().endsWith(".csv")) {
        toast.error("Please upload a CSV file (save Excel as CSV first)");
        return;
      }
      const content = await file.text();
      upload.mutate(
        { file_name: file.name, file_content: content, file_size_bytes: file.size },
        {
          onSuccess: () => {
            toast.success("File uploaded and validated");
            setPage(1);
          },
          onError: (e: Error) => toast.error(e.message),
        },
      );
    },
    [upload],
  );

  const syncToggles = useCallback(
    (nextSkip: boolean, nextMfa: boolean) => {
      settings.mutate({ skip_rows_with_errors: nextSkip, require_mfa_first_login: nextMfa });
    },
    [settings],
  );

  const handleDownloadTemplate = async () => {
    try {
      await downloadBulkInviteTemplate();
    } catch {
      toast.error("Template download failed");
    }
  };

  const handleSend = () => {
    send.mutate(undefined, {
      onSuccess: (res) => {
        toast.success(res.message);
        router.push(res.href);
      },
      onError: (e: Error) => toast.error(e.message),
    });
  };

  const hasPreview = Boolean(data?.file_name && data.pagination.total > 0);
  const isBusy = upload.isPending || send.isPending;

  const openFilePicker = () => fileRef.current?.click();

  return (
    <div className="space-y-5" data-figma-frame="69:126100">
      <input
        ref={fileRef}
        type="file"
        accept=".csv,text/csv"
        className="sr-only"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) void onFile(file);
          e.target.value = "";
        }}
      />
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <div className="flex items-center gap-1">
            <Link
              href={data?.cancel_href ?? "/college-admin/users/user-management-dashboard"}
              className="inline-flex size-8 shrink-0 items-center justify-center rounded-md text-[#374151] hover:bg-[#f3f4f6]"
              aria-label="Back"
            >
              <ChevronLeftIcon className="size-5" />
            </Link>
            <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
              {data?.page_title ?? "Bulk User Invitation"}
            </h2>
          </div>
          <p className="mt-1 pl-9 text-[14px] text-[#6b7280]">{data?.page_subtitle}</p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <button
            type="button"
            onClick={() => void handleDownloadTemplate()}
            className="inline-flex h-9 items-center gap-1.5 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb]"
          >
            <CollegeAdminDownload className="size-3.5" />
            {data?.download_template_label ?? "Download template"}
          </button>
          <button
            type="button"
            disabled={!hasPreview || isBusy || !data?.ready_to_send_count}
            onClick={handleSend}
            className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8] disabled:opacity-50"
          >
            <SendHorizontalIcon className="size-3.5" aria-hidden />
            {data?.send_invitations_label ?? "Send invitations"}
          </button>
        </div>
      </div>

      <WizardStepper
        steps={data?.steps ?? [...DEFAULT_STEPS]}
        activeKey={hasPreview ? "preview" : activeStep}
        activeIndex={hasPreview ? 2 : stepIndex}
      />

      <QueryState
        isLoading={pageQuery.isLoading}
        isError={pageQuery.isError}
        error={pageQuery.error}
        onRetry={() => void pageQuery.refetch()}
      >
        {data ? (
          <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_300px]">
            <div className="space-y-5">
              {hasPreview ? (
                <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                  <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                    <h3 className="text-[14px] font-semibold text-[#111827]">{data.preview_section_title}</h3>
                    {data.preview_summary_label ? (
                      <p className="mt-0.5 text-[12px] text-[#6b7280]">{data.preview_summary_label}</p>
                    ) : null}
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[40rem] text-left text-[13px]">
                      <thead>
                        <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                          {data.table_headers.map((h) => (
                            <th key={h} className="px-5 pb-3 pt-3 font-medium">
                              {h}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#f1f5f9]">
                        {data.preview_rows.map((row) => (
                          <tr key={row.row_id} className="hover:bg-[#f9fafb]">
                            <td className="px-5 py-3 font-medium text-[#111827]">{row.full_name}</td>
                            <td className="py-3 pr-3 text-[#374151]">{row.email}</td>
                            <td className="py-3 pr-3 text-[#374151]">{row.role_label}</td>
                            <td className="py-3 pr-3 text-[#374151]">{row.department_label}</td>
                            <td className="py-3 pr-5">
                              <StatusPill row={row} />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
                    <span>{data.pagination.showing_label}</span>
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
                        {data.pagination.page_numbers.map((num, i) =>
                          num === -1 ? (
                            <span key={`e-${i}`} className="px-1">
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
              ) : (
                <section className="rounded-xl border border-dashed border-[#dce3ec] bg-white p-8 text-center">
                  <UploadIcon className="mx-auto size-8 text-[#9ca3af]" aria-hidden />
                  <p className="mt-3 text-sm font-medium text-[#111827]">{data.upload_drop_hint}</p>
                  <button
                    type="button"
                    disabled={isBusy}
                    onClick={openFilePicker}
                    className="mt-4 inline-flex h-9 items-center rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb]"
                  >
                    {data.browse_files_label}
                  </button>
                </section>
              )}
            </div>

            <div className="space-y-5">
              <section className="rounded-xl border border-[#e8ecf2] bg-white p-4 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                {data.file_name ? (
                  <div className="flex items-start gap-3">
                    <UploadIcon className="size-5 shrink-0 text-[#245dd8]" aria-hidden />
                    <div className="min-w-0">
                      <p className="truncate text-[13px] font-semibold text-[#111827]">{data.file_name}</p>
                      <p className="text-[11px] text-[#6b7280]">{data.file_meta_label}</p>
                    </div>
                  </div>
                ) : null}
                <div
                  className={cn(
                    "mt-3 rounded-lg border border-dashed border-[#dce3ec] p-4 text-center",
                    !data.file_name && "mt-0",
                  )}
                >
                  <button
                    type="button"
                    disabled={isBusy}
                    onClick={openFilePicker}
                    className="text-xs font-medium text-[#245dd8] hover:underline"
                  >
                    {data.browse_files_label}
                  </button>
                </div>
              </section>

              {data.summary_stats.length ? (
                <section className="rounded-xl border border-[#e8ecf2] bg-white p-4 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                  <h3 className="text-[13px] font-semibold text-[#111827]">{data.validation_summary_title}</h3>
                  <div className="mt-3 space-y-2">
                    {data.summary_stats.map((stat) => (
                      <SummaryCard key={stat.key} stat={stat} />
                    ))}
                  </div>
                </section>
              ) : null}

              <section className="rounded-xl border border-[#e8ecf2] bg-white p-4 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <h3 className="text-[13px] font-semibold text-[#111827]">{data.invitation_options_title}</h3>
                <ul className="mt-3 space-y-4">
                  {data.invitation_toggles.map((toggle) => {
                    const checked =
                      toggle.key === "skip_rows_with_errors"
                        ? skipErrors
                        : toggle.key === "require_mfa_first_login"
                          ? requireMfa
                          : toggle.default_on;
                    return (
                      <li key={toggle.key} className="flex items-start justify-between gap-3">
                        <div>
                          <p className="text-[13px] font-medium text-[#111827]">{toggle.label}</p>
                          <p className="text-[11px] text-[#6b7280]">{toggle.description}</p>
                        </div>
                        <label className="relative inline-flex cursor-pointer items-center">
                          <input
                            type="checkbox"
                            className="peer sr-only"
                            checked={checked}
                            onChange={(e) => {
                              if (toggle.key === "skip_rows_with_errors") {
                                setSkipErrors(e.target.checked);
                                syncToggles(e.target.checked, requireMfa);
                              } else {
                                setRequireMfa(e.target.checked);
                                syncToggles(skipErrors, e.target.checked);
                              }
                            }}
                          />
                          <span className="h-5 w-9 rounded-full bg-[#e5e7eb] after:absolute after:left-0.5 after:top-0.5 after:size-4 after:rounded-full after:bg-white after:transition peer-checked:bg-[#245dd8] peer-checked:after:translate-x-4" />
                        </label>
                      </li>
                    );
                  })}
                </ul>
              </section>
            </div>
          </div>
        ) : null}
      </QueryState>

      {data ? (
        <footer className="flex flex-col gap-3 border-t border-[#e8ecf2] pt-4 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-[11px] text-[#9ca3af]">{data.audit_footer_note}</p>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              disabled={!hasPreview}
              onClick={() => {
                setPage(1);
                void pageQuery.refetch();
                toast.message(data.fix_errors_label, { description: "Re-upload CSV after fixing source file" });
              }}
              className="inline-flex h-9 items-center rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb] disabled:opacity-50"
            >
              {data.fix_errors_label}
            </button>
            <Link
              href={data.cancel_href}
              className="inline-flex h-9 items-center rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb]"
            >
              {data.back_label}
            </Link>
            <button
              type="button"
              disabled={!data.ready_to_send_count || isBusy}
              onClick={handleSend}
              className="inline-flex h-9 items-center rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8] disabled:opacity-50"
            >
              {data.send_ready_label}
            </button>
          </div>
        </footer>
      ) : null}

      {data ? <p className="text-[11px] text-[#9ca3af]">{data.footer_disclaimer}</p> : null}
    </div>
  );
}