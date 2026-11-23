"use client";

import Link from "next/link";
import { useCallback, useMemo, type ReactNode } from "react";
import { useForm } from "react-hook-form";

import { BookOpenIcon } from "@/components/icons/erp/generated/book-open";
import { CheckIcon } from "@/components/icons/erp/generated/check";
import { GraduationCapIcon } from "@/components/icons/erp/generated/graduation-cap";
import { IdCardIcon } from "@/components/icons/erp/generated/id-card";
import { InfoIcon } from "@/components/icons/erp/generated/info";
import { LockIcon } from "@/components/icons/erp/generated/lock";
import { ReceiptIcon } from "@/components/icons/erp/generated/receipt";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  InstitutionPageActionFooter,
  institutionActionButtonOutline,
  institutionActionButtonPrimary,
} from "@/features/college-admin/components/institution/institution-page-action-footer";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useInstitutionInformationPage,
  usePublishInstitutionInformation,
  useSaveInstitutionInformationDraft,
} from "@/features/college-admin/hooks/use-institution";
import type {
  InstitutionFieldMeta,
  InstitutionFieldOption,
  InstitutionInformationFormValues,
  InstitutionInformationPage,
} from "@/features/college-admin/types/institution";
import { normalizeFormPayload } from "@/lib/form-values";
import { cn } from "@/lib/utils";

const USAGE_ICONS = [GraduationCapIcon, ReceiptIcon, BookOpenIcon, IdCardIcon];

function metaFor(
  fieldMeta: InstitutionFieldMeta[],
  key: string,
): InstitutionFieldMeta | undefined {
  return fieldMeta.find((row) => row.key === key);
}

function FormField({
  meta,
  children,
}: {
  meta?: InstitutionFieldMeta;
  children: ReactNode;
}) {
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

function SelectInput({
  value,
  onChange,
  options,
  allowCustom,
}: {
  value: string | null | undefined;
  onChange: (v: string) => void;
  options: InstitutionFieldOption[];
  allowCustom?: boolean;
}) {
  const showCustom = allowCustom && value && !options.some((o) => o.value === value);
  return (
    <div className="relative">
      <select
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value)}
        className="h-9 w-full appearance-none rounded-md border border-[#dce3ec] bg-white px-3 pr-9 text-[13px] text-[#111827] outline-none focus:border-[#245dd8] focus:ring-1 focus:ring-[#245dd8]"
      >
        {options.map((opt) => (
          <option key={opt.value || opt.label} value={opt.value}>
            {opt.label}
          </option>
        ))}
        {showCustom ? <option value={value ?? ""}>{value}</option> : null}
      </select>
      <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-[#9ca3af]">
        ▾
      </span>
    </div>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
      <div className="border-b border-[#f1f5f9] px-5 py-3.5">
        <h3 className="text-[14px] font-semibold text-[#111827]">{title}</h3>
      </div>
      <div className="px-5 py-2">{children}</div>
    </section>
  );
}

function buildDefaults(page: InstitutionInformationPage): InstitutionInformationFormValues {
  const f = page.form;
  return {
    ...f,
    autonomous_status_valid_until: f.autonomous_status_valid_until
      ? f.autonomous_status_valid_until.slice(0, 10)
      : null,
  };
}

function toPayload(values: InstitutionInformationFormValues): Record<string, unknown> {
  const normalized = normalizeFormPayload(values as Record<string, unknown>);
  return normalizeFormPayload({
    ...normalized,
    display_name: normalized.legal_name ?? values.legal_name,
    year_established:
      values.year_established !== null && values.year_established !== undefined
        ? Number(values.year_established)
        : null,
    autonomous_status_valid_until: values.autonomous_status_valid_until || null,
  });
}

export function InstitutionInformationForm() {
  const pageQuery = useInstitutionInformationPage();
  const saveDraft = useSaveInstitutionInformationDraft();
  const publish = usePublishInstitutionInformation();

  const defaults = useMemo(
    () => (pageQuery.data ? buildDefaults(pageQuery.data) : undefined),
    [pageQuery.data],
  );

  const form = useForm<InstitutionInformationFormValues>({
    values: defaults,
  });

  const submitPublish = form.handleSubmit((values) => {
    publish.mutate(toPayload(values));
  });

  const handleSaveDraft = form.handleSubmit((values) => {
    saveDraft.mutate(toPayload(values));
  });

  const discard = useCallback(() => {
    if (pageQuery.data) {
      form.reset(buildDefaults(pageQuery.data));
    }
  }, [form, pageQuery.data]);

  const data = pageQuery.data;
  const fieldMeta = data?.field_meta ?? [];
  const isBusy = saveDraft.isPending || publish.isPending;

  return (
    <div className="space-y-5" data-figma-frame="72:6332">
      <MotionHeader>
        <div className="min-w-0">
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            Institution Information
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">
            Edit the official details shown on certificates, receipts and reports.
          </p>
        </div>
      </MotionHeader>

      <QueryState
        isLoading={pageQuery.isLoading}
        isError={pageQuery.isError}
        error={pageQuery.error}
        onRetry={() => void pageQuery.refetch()}
      >
        {data ? (
          <>
            <MotionBanner notice={data.approval_notice} />

            <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_392px]">
              <form className="space-y-5" onSubmit={(e) => e.preventDefault()}>
                <Section title="Basic details">
                  <div className="grid gap-x-6 gap-y-1 sm:grid-cols-2">
                    <FormField meta={metaFor(fieldMeta, "legal_name")}>
                      <Input
                        {...form.register("legal_name")}
                        className="border-[#dce3ec] text-[13px]"
                      />
                    </FormField>
                    <FormField meta={metaFor(fieldMeta, "short_name")}>
                      <Input
                        {...form.register("short_name")}
                        className="border-[#dce3ec] text-[13px]"
                      />
                    </FormField>
                    <FormField meta={metaFor(fieldMeta, "institution_code")}>
                      <div className="relative">
                        <Input
                          {...form.register("institution_code")}
                          readOnly={metaFor(fieldMeta, "institution_code")?.locked}
                          className="border-[#dce3ec] pr-9 text-[13px] read-only:bg-[#f9fafb] read-only:text-[#6b7280]"
                        />
                        <LockIcon
                          className="pointer-events-none absolute right-3 top-1/2 size-3.5 -translate-y-1/2 text-[#9ca3af]"
                          aria-hidden
                        />
                      </div>
                    </FormField>
                    <FormField meta={metaFor(fieldMeta, "year_established")}>
                      <Input
                        type="number"
                        {...form.register("year_established", { valueAsNumber: true })}
                        className="border-[#dce3ec] text-[13px]"
                      />
                    </FormField>
                    <FormField meta={metaFor(fieldMeta, "institution_type")}>
                      <SelectInput
                        value={form.watch("institution_type")}
                        onChange={(v) => form.setValue("institution_type", v || null)}
                        options={data.institution_type_options}
                        allowCustom
                      />
                    </FormField>
                    <FormField meta={metaFor(fieldMeta, "medium_of_instruction")}>
                      <SelectInput
                        value={form.watch("medium_of_instruction")}
                        onChange={(v) => form.setValue("medium_of_instruction", v || null)}
                        options={data.medium_of_instruction_options}
                        allowCustom
                      />
                    </FormField>
                  </div>
                  <FormField meta={metaFor(fieldMeta, "description")}>
                    <textarea
                      {...form.register("description")}
                      rows={3}
                      className="mt-4 w-full resize-y rounded-md border border-[#dce3ec] px-3 py-2 text-[13px] text-[#111827] outline-none focus:border-[#245dd8] focus:ring-1 focus:ring-[#245dd8]"
                    />
                  </FormField>
                </Section>

                <Section title="Registration & affiliation">
                  <div className="grid gap-x-6 gap-y-1 sm:grid-cols-2">
                    <FormField meta={metaFor(fieldMeta, "affiliation_name")}>
                      <SelectInput
                        value={form.watch("affiliation_name")}
                        onChange={(v) => form.setValue("affiliation_name", v || null)}
                        options={data.affiliation_options}
                        allowCustom
                      />
                    </FormField>
                    <FormField meta={metaFor(fieldMeta, "autonomous_status_valid_until")}>
                      <Input
                        type="date"
                        {...form.register("autonomous_status_valid_until")}
                        className="border-[#dce3ec] text-[13px]"
                      />
                    </FormField>
                    <FormField meta={metaFor(fieldMeta, "affiliation_id")}>
                      <Input
                        {...form.register("affiliation_id")}
                        className="border-[#dce3ec] text-[13px]"
                      />
                    </FormField>
                    <FormField meta={metaFor(fieldMeta, "aishe_code")}>
                      <Input
                        {...form.register("aishe_code")}
                        className="border-[#dce3ec] text-[13px]"
                      />
                    </FormField>
                    <FormField meta={metaFor(fieldMeta, "ugc_recognition")}>
                      <SelectInput
                        value={form.watch("ugc_recognition")}
                        onChange={(v) => form.setValue("ugc_recognition", v || null)}
                        options={data.ugc_recognition_options}
                      />
                    </FormField>
                    <FormField meta={metaFor(fieldMeta, "ownership_name")}>
                      <Input
                        {...form.register("ownership_name")}
                        className="border-[#dce3ec] text-[13px]"
                      />
                    </FormField>
                  </div>
                </Section>

                <Section title="Contact details">
                  <div className="grid gap-x-6 gap-y-1 sm:grid-cols-2">
                    <FormField meta={metaFor(fieldMeta, "institution_email")}>
                      <Input
                        type="email"
                        {...form.register("institution_email")}
                        className="border-[#dce3ec] text-[13px]"
                      />
                    </FormField>
                    <FormField meta={metaFor(fieldMeta, "contact_phone")}>
                      <Input
                        {...form.register("contact_phone")}
                        className="border-[#dce3ec] text-[13px]"
                      />
                    </FormField>
                    <FormField meta={metaFor(fieldMeta, "official_website")}>
                      <Input
                        {...form.register("official_website")}
                        className="border-[#dce3ec] text-[13px]"
                      />
                    </FormField>
                    <FormField meta={metaFor(fieldMeta, "contact_fax")}>
                      <Input
                        {...form.register("contact_fax")}
                        placeholder="Optional"
                        className="border-[#dce3ec] text-[13px]"
                      />
                    </FormField>
                  </div>
                </Section>
              </form>

              <div className="space-y-5">
                <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                  <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                    <h3 className="text-[14px] font-semibold text-[#111827]">Where this appears</h3>
                  </div>
                  <ul className="divide-y divide-[#f1f5f9] px-5">
                    {data.usage_contexts.map((item, index) => {
                      const Icon = USAGE_ICONS[index % USAGE_ICONS.length];
                      return (
                        <li key={item.title} className="flex gap-3 py-3.5 first:pt-3">
                          <Icon className="mt-0.5 size-[18px] shrink-0 text-[#9ca3af]" aria-hidden />
                          <div>
                            <p className="text-[13px] font-medium text-[#111827]">{item.title}</p>
                            <p className="text-[12px] text-[#6b7280]">{item.description}</p>
                          </div>
                        </li>
                      );
                    })}
                  </ul>
                </section>

                <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                  <div className="flex items-center justify-between gap-2 border-b border-[#f1f5f9] px-5 py-3.5">
                    <h3 className="text-[14px] font-semibold text-[#111827]">Recent changes</h3>
                    <Link
                      href={data.history_href}
                      className="text-[12px] font-medium text-[#245dd8] hover:underline"
                    >
                      History →
                    </Link>
                  </div>
                  {data.recent_changes.length ? (
                    <ul className="px-5 py-2">
                      {data.recent_changes.map((row) => (
                        <li key={row.change_id} className="flex gap-3 py-3">
                          <span
                            className={cn(
                              "mt-1.5 size-2 shrink-0 rounded-full",
                              row.tone === "info" ? "bg-[#3b82f6]" : "bg-[#10b981]",
                            )}
                          />
                          <div>
                            <p className="text-[13px] font-medium text-[#111827]">{row.title}</p>
                            <p className="text-[12px] text-[#6b7280]">{row.detail_line}</p>
                          </div>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="px-5 py-4 text-sm text-[#9ca3af]">No profile changes recorded yet.</p>
                  )}
                </section>
              </div>
            </div>

            <InstitutionPageActionFooter note={data.footer_note}>
              <Button
                type="button"
                variant="outline"
                className={institutionActionButtonOutline}
                onClick={discard}
                disabled={isBusy}
              >
                Cancel
              </Button>
              <Button
                type="button"
                variant="outline"
                className={institutionActionButtonOutline}
                onClick={() => void handleSaveDraft()}
                disabled={isBusy}
              >
                Save draft
              </Button>
              <Button
                type="button"
                className={institutionActionButtonPrimary}
                onClick={() => void submitPublish()}
                disabled={isBusy}
              >
                <CheckIcon className="size-3.5" aria-hidden />
                Save changes
              </Button>
            </InstitutionPageActionFooter>
          </>
        ) : null}
      </QueryState>
    </div>
  );
}

function MotionHeader({ children }: { children: ReactNode }) {
  return <>{children}</>;
}

function MotionBanner({
  notice,
}: {
  notice: { title: string; body: string };
}) {
  return (
    <div className="flex gap-3 rounded-xl border border-[#bfdbfe] bg-[#eff6ff] px-4 py-3.5">
      <InfoIcon className="mt-0.5 size-[18px] shrink-0 text-[#2563eb]" aria-hidden />
      <div className="min-w-0 text-[13px] leading-relaxed text-[#1e3a8a]">
        <p className="font-semibold text-[#1d4ed8]">{notice.title}</p>
        <p className="mt-0.5 text-[12px] text-[#1e40af]">{notice.body}</p>
      </div>
    </div>
  );
}