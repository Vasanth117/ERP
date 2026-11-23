"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useMemo } from "react";
import { useForm } from "react-hook-form";
import { useMutation } from "@tanstack/react-query";
import { onCollegeAdminMutationError } from "@/features/college-admin/context/college-admin-validation-context";
import { toast } from "sonner";

import { BanIcon } from "@/components/icons/erp/generated/ban";
import { CheckIcon } from "@/components/icons/erp/generated/check";
import { ChevronLeftIcon } from "@/components/icons/erp/generated/chevron-left";
import { LockIcon } from "@/components/icons/erp/generated/lock";
import { XIcon } from "@/components/icons/erp/generated/x";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useEditUserInformationPage,
  useSaveEditUserInformation,
} from "@/features/college-admin/hooks/use-edit-user-information";
import { revokeUserSessions } from "@/features/college-admin/api/users";
import type { EditUserInformationFormValues } from "@/features/college-admin/types/edit-user-information";
import type { InstitutionFieldMeta } from "@/features/college-admin/types/institution";
import { cn } from "@/lib/utils";

function metaFor(fieldMeta: InstitutionFieldMeta[], key: string) {
  return fieldMeta.find((row) => row.key === key);
}

function FormField({ meta, children }: { meta?: InstitutionFieldMeta; children: React.ReactNode }) {
  if (!meta) return null;
  return (
    <div className="space-y-1.5">
      <Label className="text-[13px] font-medium text-[#374151]">
        {meta.label}
        {meta.required ? <span className="text-[#dc2626]"> *</span> : null}
      </Label>
      {children}
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
      <div className="border-b border-[#f1f5f9] px-5 py-3.5">
        <h3 className="text-[14px] font-semibold text-[#111827]">{title}</h3>
      </div>
      <div className="px-5 py-4">{children}</div>
    </section>
  );
}

function StatusBadge({ label, tone }: { label: string; tone: string }) {
  const styles: Record<string, string> = {
    success: "bg-[#ecfdf5] text-[#047857]",
    error: "bg-[#fef2f2] text-[#b91c1c]",
    info: "bg-[#eff6ff] text-[#1d4ed8]",
    muted: "bg-[#f3f4f6] text-[#6b7280]",
  };
  const key = tone in styles ? tone : "muted";
  return <span className={cn("rounded-full px-2.5 py-0.5 text-[11px] font-medium", styles[key])}>{label}</span>;
}

export function EditUserInformationDashboard() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const userId = useMemo(
    () => searchParams.get("userId") ?? searchParams.get("user_id") ?? "",
    [searchParams],
  );

  const pageQuery = useEditUserInformationPage(userId || null);
  const saveMutation = useSaveEditUserInformation(userId);

  const form = useForm<EditUserInformationFormValues>({
    values: pageQuery.data?.form,
  });

  const data = pageQuery.data;

  const discard = useCallback(() => {
    if (data) {
      form.reset(data.form);
    }
  }, [data, form]);

  const submitSave = form.handleSubmit((values) => {
    saveMutation.mutate(values as unknown as Record<string, unknown>, {
      onSuccess: () => {
        toast.success("Changes saved");
        router.push(data?.detail_href ?? `/college-admin/users/user-details?userId=${userId}`);
      },
      onError: onCollegeAdminMutationError,
    });
  });

  const revokeSessions = useMutation({
    mutationFn: () => revokeUserSessions(userId),
    onSuccess: () => toast.success("Sessions revoked"),
    onError: onCollegeAdminMutationError,
  });

  if (!userId) {
    return (
      <p className="text-sm text-[#6b7280]">
        Open this page from{" "}
        <Link href="/college-admin/users/all-users-list" className="text-[#245dd8] hover:underline">
          a user profile
        </Link>
        .
      </p>
    );
  }

  const isBusy = saveMutation.isPending;

  return (
    <div className="space-y-5" data-figma-frame="69:125909">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="flex min-w-0 items-start gap-3">
          <Link
            href={data?.detail_href ?? `/college-admin/users/user-details?userId=${userId}`}
            className="mt-1 inline-flex size-8 items-center justify-center rounded-md border border-[#e5e7eb] bg-white text-[#374151] hover:bg-[#f9fafb]"
            aria-label="Back to user details"
          >
            <ChevronLeftIcon className="size-4" />
          </Link>
          <div>
            <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
              {data?.page_title ?? "Edit User Information"}
            </h2>
            <p className="mt-1 text-[14px] text-[#6b7280]">{data?.page_subtitle}</p>
          </div>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <button
            type="button"
            disabled={!data || isBusy}
            onClick={discard}
            className="inline-flex h-9 items-center gap-1.5 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb] disabled:opacity-50"
          >
            <XIcon className="size-3.5" aria-hidden />
            {data?.discard_label ?? "Discard"}
          </button>
          <button
            type="button"
            disabled={!data || isBusy}
            onClick={() => void submitSave()}
            className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8] disabled:opacity-50"
          >
            <CheckIcon className="size-3.5" aria-hidden />
            {data?.save_label ?? "Save changes"}
          </button>
        </div>
      </div>

      <QueryState
        isLoading={pageQuery.isLoading}
        isError={pageQuery.isError}
        error={pageQuery.error}
        onRetry={() => void pageQuery.refetch()}
      >
        {data ? (
          <>
            <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_300px]">
              <div className="space-y-5">
                <Section title={data.profile_section_title}>
                  <div className="grid gap-4 sm:grid-cols-2">
                    <FormField meta={metaFor(data.profile_field_meta, "full_name")}>
                      <Input className="h-9" {...form.register("full_name")} />
                    </FormField>
                    <FormField meta={metaFor(data.profile_field_meta, "display_name")}>
                      <Input className="h-9" {...form.register("display_name")} />
                    </FormField>
                    <FormField meta={metaFor(data.profile_field_meta, "official_email")}>
                      <Input className="h-9" type="email" {...form.register("official_email")} />
                    </FormField>
                    <FormField meta={metaFor(data.profile_field_meta, "personal_email")}>
                      <Input className="h-9" type="email" placeholder="Optional" {...form.register("personal_email")} />
                    </FormField>
                    <FormField meta={metaFor(data.profile_field_meta, "mobile_number")}>
                      <Input className="h-9" {...form.register("mobile_number")} />
                    </FormField>
                    <FormField meta={metaFor(data.profile_field_meta, "alternate_phone")}>
                      <Input className="h-9" placeholder="Optional" {...form.register("alternate_phone")} />
                    </FormField>
                    <FormField meta={metaFor(data.profile_field_meta, "department_id")}>
                      <select
                        className="h-9 w-full rounded-md border border-[#dce3ec] px-3 text-[13px]"
                        {...form.register("department_id")}
                      >
                        {data.department_options.map((opt) => (
                          <option key={opt.value || opt.label} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                    </FormField>
                    <FormField meta={metaFor(data.profile_field_meta, "designation")}>
                      <select
                        className="h-9 w-full rounded-md border border-[#dce3ec] px-3 text-[13px]"
                        {...form.register("designation")}
                      >
                        {data.designation_options.map((opt) => (
                          <option key={opt.value || opt.label} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                    </FormField>
                  </div>
                </Section>

                <Section title={data.login_section_title}>
                  <div className="grid gap-4 sm:grid-cols-2">
                    <FormField meta={metaFor(data.login_field_meta, "username")}>
                      <div className="relative">
                        <LockIcon
                          className="pointer-events-none absolute left-3 top-1/2 size-3.5 -translate-y-1/2 text-[#9ca3af]"
                          aria-hidden
                        />
                        <Input className="h-9 bg-[#f9fafb] pl-9" readOnly {...form.register("username")} />
                      </div>
                    </FormField>
                    <FormField meta={metaFor(data.login_field_meta, "login_method")}>
                      <select
                        className="h-9 w-full rounded-md border border-[#dce3ec] px-3 text-[13px]"
                        {...form.register("login_method")}
                      >
                        {data.login_method_options.map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                    </FormField>
                    <FormField meta={metaFor(data.login_field_meta, "mfa_requirement")}>
                      <select
                        className="h-9 w-full rounded-md border border-[#dce3ec] px-3 text-[13px]"
                        {...form.register("mfa_requirement")}
                      >
                        {data.mfa_options.map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                    </FormField>
                    <FormField meta={metaFor(data.login_field_meta, "session_timeout_minutes")}>
                      <select
                        className="h-9 w-full rounded-md border border-[#dce3ec] px-3 text-[13px]"
                        value={String(form.watch("session_timeout_minutes"))}
                        onChange={(e) => form.setValue("session_timeout_minutes", Number(e.target.value))}
                      >
                        {data.session_timeout_options.map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                    </FormField>
                  </div>
                </Section>
              </div>

              <div className="space-y-5">
                <Section title={data.account_status_section_title}>
                  <dl className="space-y-3 text-[13px]">
                    <div className="flex items-center justify-between gap-2">
                      <dt className="text-[#6b7280]">Status</dt>
                      <dd>
                        <StatusBadge
                          label={data.account_status.status_label}
                          tone={data.account_status.status_tone}
                        />
                      </dd>
                    </div>
                    <div>
                      <dt className="text-[#6b7280]">Created</dt>
                      <dd className="mt-1 font-medium text-[#111827]">{data.account_status.created_label}</dd>
                    </div>
                    <div>
                      <dt className="text-[#6b7280]">Last modified</dt>
                      <dd className="mt-1 font-medium text-[#111827]">{data.account_status.last_modified_label}</dd>
                    </div>
                  </dl>
                </Section>

                <Section title={data.danger_zone_title}>
                  <ul className="divide-y divide-[#f1f5f9]">
                    {data.danger_actions.map((action) => (
                      <li key={action.key} className="flex items-start gap-3 py-3 first:pt-0 last:pb-0">
                        {action.icon === "ban" ? (
                          <BanIcon className="mt-0.5 size-4 text-[#ef4444]" aria-hidden />
                        ) : (
                          <LockIcon className="mt-0.5 size-4 text-[#6b7280]" aria-hidden />
                        )}
                        <div className="min-w-0 flex-1">
                          <p className="text-[13px] font-medium text-[#111827]">{action.title}</p>
                          <p className="text-[11px] text-[#6b7280]">{action.description}</p>
                        </div>
                        {action.api_action === "revoke_sessions" ? (
                          <button
                            type="button"
                            className="shrink-0 text-[12px] font-medium text-[#245dd8] hover:underline"
                            disabled={revokeSessions.isPending}
                            onClick={() => revokeSessions.mutate()}
                          >
                            {action.action_label} →
                          </button>
                        ) : (
                          <Link
                            href={action.href}
                            className="shrink-0 text-[12px] font-medium text-[#245dd8] hover:underline"
                          >
                            {action.action_label} →
                          </Link>
                        )}
                      </li>
                    ))}
                  </ul>
                </Section>
              </div>
            </div>

            <footer className="flex flex-col gap-3 border-t border-[#e8ecf2] pt-4 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-[11px] text-[#9ca3af]">{data.audit_footer_note}</p>
              <div className="flex flex-wrap gap-2">
                <Link
                  href={data.detail_href}
                  className="inline-flex h-9 items-center rounded-md border border-transparent px-4 text-xs font-medium text-[#6b7280] hover:text-[#374151]"
                >
                  {data.cancel_label}
                </Link>
                <button
                  type="button"
                  disabled={isBusy}
                  onClick={() => void submitSave()}
                  className="inline-flex h-9 items-center rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8] disabled:opacity-50"
                >
                  {data.save_label}
                </button>
              </div>
            </footer>

          </>
        ) : null}
      </QueryState>
    </div>
  );
}