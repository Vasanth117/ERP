"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useCallback, useMemo } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { CalendarIcon } from "@/components/icons/erp/generated/calendar";
import { CheckIcon } from "@/components/icons/erp/generated/check";
import { LockIcon } from "@/components/icons/erp/generated/lock";
import { MailIcon } from "@/components/icons/erp/generated/mail";
import { PhoneIcon } from "@/components/icons/erp/generated/phone";
import { XIcon } from "@/components/icons/erp/generated/x";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useEmployeeProfileManagementPage,
  useSaveEmployeeProfileManagement,
} from "@/features/college-admin/hooks/use-employee-profile-management";
import type { EmployeeProfileManagementFormValues } from "@/features/college-admin/types/employee-profile-management";
import type { InstitutionFieldMeta } from "@/features/college-admin/types/institution";
import { cn } from "@/lib/utils";

function metaFor(fieldMeta: InstitutionFieldMeta[], key: string) {
  return fieldMeta.find((row) => row.key === key);
}

function FormField({ meta, children }: { meta?: InstitutionFieldMeta; children: React.ReactNode }) {
  if (!meta) return null;
  return (
    <div className={cn("space-y-1.5", meta.field_type === "textarea" ? "sm:col-span-2" : undefined)}>
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

function Badge({ label, tone }: { label: string; tone: string }) {
  const styles: Record<string, string> = {
    success: "bg-[#ecfdf5] text-[#047857]",
    warning: "bg-[#fff7ed] text-[#c2410c]",
    error: "bg-[#fef2f2] text-[#b91c1c]",
    info: "bg-[#eff6ff] text-[#1d4ed8]",
    muted: "bg-[#f3f4f6] text-[#6b7280]",
  };
  const key = tone in styles ? tone : "muted";
  return (
    <span className={cn("rounded-full px-2.5 py-0.5 text-[11px] font-medium", styles[key])}>{label}</span>
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

export function EmployeeProfileManagementDashboard() {
  const searchParams = useSearchParams();
  const recordId = useMemo(
    () => searchParams.get("record_id") ?? searchParams.get("id") ?? undefined,
    [searchParams],
  );

  const pageQuery = useEmployeeProfileManagementPage(recordId);
  const saveMutation = useSaveEmployeeProfileManagement(recordId ?? "");

  const form = useForm<EmployeeProfileManagementFormValues>({
    values: pageQuery.data?.form,
  });

  const data = pageQuery.data;
  const saveRecordId = data?.record_id ?? recordId ?? "";

  const discard = useCallback(() => {
    if (data?.form) {
      form.reset(data.form);
    }
  }, [data?.form, form]);

  const submitSave = form.handleSubmit((values) => {
    if (!saveRecordId) return;
    saveMutation.mutate(values as unknown as Record<string, unknown>, {
      onSuccess: () => toast.success("Profile changes saved"),
      onError: (e: Error) => toast.error(e.message),
    });
  });

  const isBusy = saveMutation.isPending;

  return (
    <div className="space-y-5" data-figma-frame="158:3788">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Employee Profile Management"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">
            {data?.page_subtitle ?? "Update an employee record"}
          </p>
        </div>
        {!data?.requires_record ? (
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
              {data?.save_changes_label ?? "Save changes"}
            </button>
          </div>
        ) : null}
      </div>

      <QueryState
        isLoading={pageQuery.isLoading}
        isError={pageQuery.isError}
        error={pageQuery.error}
        onRetry={() => void pageQuery.refetch()}
      >
        {data?.requires_record ? (
          <Section title={data.select_employee_title ?? "Select an employee"}>
            <p className="mb-4 text-sm text-[#6b7280]">{data.select_employee_hint}</p>
            {data.picker_rows.length ? (
              <ul className="divide-y divide-[#f1f5f9] rounded-lg border border-[#e8ecf2]">
                {data.picker_rows.map((row) => (
                  <li key={row.record_id}>
                    <Link
                      href={row.manage_href}
                      className="flex items-center justify-between gap-4 px-4 py-3 text-[13px] hover:bg-[#f9fafb]"
                    >
                      <span className="font-medium text-[#111827]">{row.employee_name}</span>
                      <span className="font-mono text-[#6b7280]">{row.employee_id_label}</span>
                    </Link>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-[#9ca3af]">No employee records yet.</p>
            )}
            {data.employee_directory_href ? (
              <Link
                href={data.employee_directory_href}
                className="mt-4 inline-flex text-sm font-medium text-[#245dd8] hover:underline"
              >
                {data.employee_directory_label} →
              </Link>
            ) : null}
          </Section>
        ) : data ? (
          <>
            <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
                <div
                  className="flex size-14 shrink-0 items-center justify-center rounded-full bg-[#eff6ff] text-[16px] font-semibold text-[#245dd8]"
                  aria-hidden
                >
                  {data.profile_initials}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="text-[18px] font-bold text-[#111827]">{data.profile_name}</h3>
                    {data.profile_badges.map((badge) => (
                      <Badge key={badge.key} label={badge.label} tone={badge.tone} />
                    ))}
                  </div>
                  <p className="mt-1 text-[13px] text-[#6b7280]">{data.profile_summary_line}</p>
                  <div className="mt-3 flex flex-wrap gap-x-5 gap-y-2 text-[12px] text-[#374151]">
                    <span className="inline-flex items-center gap-1.5">
                      <MailIcon className="size-3.5 text-[#9ca3af]" aria-hidden />
                      {data.email_display}
                    </span>
                    <span className="inline-flex items-center gap-1.5">
                      <PhoneIcon className="size-3.5 text-[#9ca3af]" aria-hidden />
                      {data.phone_display}
                    </span>
                    <span className="inline-flex items-center gap-1.5">
                      <CalendarIcon className="size-3.5 text-[#9ca3af]" aria-hidden />
                      {data.joined_label}
                    </span>
                  </div>
                </div>
              </div>
            </section>

            <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_300px]">
              <Section title={data.editable_section_title}>
                <form
                  className="grid gap-4 sm:grid-cols-2"
                  onSubmit={(event) => {
                    event.preventDefault();
                    void submitSave();
                  }}
                >
                  <FormField meta={metaFor(data.field_meta, "full_name")}>
                    <Input className="h-9" {...form.register("full_name")} />
                  </FormField>
                  <FormField meta={metaFor(data.field_meta, "mobile")}>
                    <Input className="h-9" {...form.register("mobile")} />
                  </FormField>
                  <FormField meta={metaFor(data.field_meta, "official_email")}>
                    <Input className="h-9" type="email" {...form.register("official_email")} />
                  </FormField>
                  <FormField meta={metaFor(data.field_meta, "emergency_contact")}>
                    <Input className="h-9" {...form.register("emergency_contact")} />
                  </FormField>
                  <FormField meta={metaFor(data.field_meta, "address")}>
                    <textarea
                      className="min-h-[5rem] w-full rounded-md border border-[#dce3ec] px-3 py-2 text-[13px]"
                      {...form.register("address")}
                    />
                  </FormField>
                  <FormField meta={metaFor(data.field_meta, "reason_for_change")}>
                    <textarea
                      className="min-h-[5rem] w-full rounded-md border border-[#dce3ec] px-3 py-2 text-[13px]"
                      {...form.register("reason_for_change")}
                    />
                  </FormField>
                </form>
              </Section>

              <div className="space-y-5">
                <Section title={data.locked_fields_title}>
                  <ul className="space-y-4">
                    {data.locked_fields.map((field) => (
                      <li key={field.label} className="flex gap-3">
                        <LockIcon className="mt-0.5 size-4 shrink-0 text-[#9ca3af]" aria-hidden />
                        <div>
                          <p className="text-[13px] font-medium text-[#111827]">{field.label}</p>
                          <p className="text-[11px] text-[#9ca3af]">{field.subtitle}</p>
                        </div>
                      </li>
                    ))}
                  </ul>
                </Section>

                {data.last_updated ? (
                  <Section title={data.last_updated_title}>
                    <dl className="space-y-2 text-[13px]">
                      <div>
                        <dt className="text-[#6b7280]">By</dt>
                        <dd className="font-medium text-[#111827]">{data.last_updated.updated_by_label}</dd>
                      </div>
                      <div>
                        <dt className="text-[#6b7280]">On</dt>
                        <dd className="font-medium tabular-nums text-[#111827]">
                          {data.last_updated.updated_at_label}
                        </dd>
                      </div>
                    </dl>
                  </Section>
                ) : null}
              </div>
            </div>

            <footer className="flex flex-col gap-2 border-t border-[#e8ecf2] pt-4 text-[11px] text-[#9ca3af] sm:flex-row sm:items-center sm:justify-between">
              <p>
                {data.footer_disclaimer} · {data.audit_footer_note}
              </p>
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