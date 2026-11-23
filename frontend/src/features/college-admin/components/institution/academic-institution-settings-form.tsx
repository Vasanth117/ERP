"use client";

import Link from "next/link";
import { useEffect, useMemo } from "react";
import { useForm } from "react-hook-form";

import { CheckIcon } from "@/components/icons/erp/generated/check";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  CollegeAdminRefreshCw,
  getCollegeAdminErpIcon,
  resolveCollegeAdminIconSlug,
} from "@/features/college-admin/components/layout/college-admin-erp-icons";
import {
  InstitutionPageActionFooter,
  institutionActionButtonOutline,
  institutionActionButtonPrimary,
} from "@/features/college-admin/components/institution/institution-page-action-footer";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useAcademicInstitutionSettingsPage,
  useResetAcademicInstitutionSettingsPage,
  useSaveAcademicInstitutionSettingsPage,
} from "@/features/college-admin/hooks/use-institution";
import type {
  AcademicInstitutionFormValues,
  AcademicInstitutionSettingsPage,
  AcademicInstitutionToggleRule,
  InstitutionFieldMeta,
  InstitutionFieldOption,
} from "@/features/college-admin/types/institution";
import { cn } from "@/lib/utils";

function metaFor(meta: InstitutionFieldMeta[], key: string) {
  return meta.find((row) => row.key === key);
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
      <div className="border-b border-[#f1f5f9] px-5 py-3.5">
        <h3 className="text-[14px] font-semibold text-[#111827]">{title}</h3>
      </div>
      <div className="grid gap-4 px-5 py-4 sm:grid-cols-2">{children}</div>
    </section>
  );
}

function FieldControl({
  fieldKey,
  meta,
  options,
  register,
  watch,
  setValue,
}: {
  fieldKey: keyof AcademicInstitutionFormValues;
  meta?: InstitutionFieldMeta;
  options?: InstitutionFieldOption[];
  register: ReturnType<typeof useForm<AcademicInstitutionFormValues>>["register"];
  watch: ReturnType<typeof useForm<AcademicInstitutionFormValues>>["watch"];
  setValue: ReturnType<typeof useForm<AcademicInstitutionFormValues>>["setValue"];
}) {
  if (!meta) return null;
  const isSelect = meta.field_type === "select" && options?.length;
  return (
    <div className={cn(fieldKey === "condonation_band" ? "sm:col-span-2" : "")}>
      <Label className="text-[13px] text-[#374151]">
        {meta.label}
        {meta.required ? <span className="text-[#dc2626]"> *</span> : null}
      </Label>
      {isSelect ? (
        <select
          className="mt-1.5 h-9 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px]"
          value={String(watch(fieldKey) ?? "")}
          onChange={(e) => setValue(fieldKey, e.target.value, { shouldDirty: true })}
        >
          {options.map((opt) => (
            <option key={opt.value || opt.label} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      ) : (
        <Input className="mt-1.5 h-9" {...register(fieldKey)} />
      )}
    </div>
  );
}

function ToggleRow({
  rule,
  checked,
  onChange,
}: {
  rule: AcademicInstitutionToggleRule;
  checked: boolean;
  onChange: (next: boolean) => void;
}) {
  return (
    <div className="flex items-start justify-between gap-3 py-3.5 first:pt-1">
      <div>
        <p className="text-[13px] font-medium text-[#111827]">{rule.label}</p>
        <p className="text-[12px] text-[#6b7280]">{rule.description}</p>
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={cn(
          "relative h-6 w-11 shrink-0 rounded-full transition-colors",
          checked ? "bg-[#245dd8]" : "bg-[#d1d5db]",
        )}
      >
        <span
          className={cn(
            "absolute top-0.5 size-5 rounded-full bg-white shadow transition-transform",
            checked ? "left-[22px]" : "left-0.5",
          )}
        />
      </button>
    </div>
  );
}

function AppliesPanel({ page }: { page: AcademicInstitutionSettingsPage }) {
  return (
    <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
      <div className="border-b border-[#f1f5f9] px-5 py-3.5">
        <h3 className="text-[14px] font-semibold text-[#111827]">Applies to</h3>
      </div>
      <ul className="divide-y divide-[#f1f5f9] px-5">
        {page.applies_to.map((row) => {
          const Icon = getCollegeAdminErpIcon(resolveCollegeAdminIconSlug(row.icon_slug));
          const body = (
            <span className="flex min-w-0 flex-1 gap-3 py-3.5">
              {Icon ? <Icon className="mt-0.5 size-[18px] shrink-0 text-[#9ca3af]" aria-hidden /> : null}
              <span className="min-w-0">
                <span className="flex flex-wrap items-center gap-2">
                  <span className="text-[13px] font-medium text-[#111827]">{row.title}</span>
                  {row.badge_label ? (
                    <span className="inline-flex items-center gap-1 rounded-full bg-[#fff7ed] px-2 py-0.5 text-[10px] font-medium text-[#c2410c]">
                      <span className="size-1.5 rounded-full bg-[#f97316]" />
                      {row.badge_label}
                    </span>
                  ) : null}
                </span>
                <span className="block text-[12px] text-[#6b7280]">{row.description}</span>
              </span>
            </span>
          );
          return (
            <li key={row.key}>
              {row.href ? (
                <Link href={row.href} className="flex hover:bg-[#fafafa]">
                  {body}
                </Link>
              ) : (
                body
              )}
            </li>
          );
        })}
      </ul>
    </section>
  );
}

export function AcademicInstitutionSettingsForm() {
  const { data, isLoading, isError, error, refetch } = useAcademicInstitutionSettingsPage();
  const save = useSaveAcademicInstitutionSettingsPage();
  const reset = useResetAcademicInstitutionSettingsPage();

  const defaults = useMemo(() => data?.form, [data?.form]);
  const form = useForm<AcademicInstitutionFormValues>({ defaultValues: defaults });

  useEffect(() => {
    if (defaults) form.reset(defaults);
  }, [defaults, form]);

  return (
    <div className="space-y-5" data-figma-frame="72:8395">
      <div className="min-w-0">
        <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
          {data?.page_title ?? "Academic Institution Settings"}
        </h2>
        <p className="mt-1 max-w-2xl text-[14px] text-[#6b7280]">
          {data?.page_subtitle ??
            "College-wide academic rules applied to every department and programme"}
        </p>
      </div>

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <form
            onSubmit={form.handleSubmit((values) => save.mutate(values))}
            className="space-y-5"
          >
            <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_340px]">
            <div className="space-y-5">
              {data.field_groups.map((group) => (
                <Section key={group.key} title={group.title}>
                  {group.field_keys.map((fieldKey) => (
                    <FieldControl
                      key={fieldKey}
                      fieldKey={fieldKey as keyof AcademicInstitutionFormValues}
                      meta={metaFor(data.field_meta, fieldKey)}
                      options={data.field_options[fieldKey]}
                      register={form.register}
                      watch={form.watch}
                      setValue={form.setValue}
                    />
                  ))}
                </Section>
              ))}
            </div>

            <div className="space-y-5">
              <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                  <h3 className="text-[14px] font-semibold text-[#111827]">Rules</h3>
                </div>
                <div className="divide-y divide-[#f1f5f9] px-5">
                  {data.toggle_rules.map((rule) => (
                    <ToggleRow
                      key={rule.key}
                      rule={rule}
                      checked={Boolean(
                        form.watch(rule.key as keyof AcademicInstitutionFormValues),
                      )}
                      onChange={(next) =>
                        form.setValue(
                          rule.key as keyof AcademicInstitutionFormValues,
                          next as never,
                          { shouldDirty: true },
                        )
                      }
                    />
                  ))}
                </div>
              </section>

              <AppliesPanel page={data} />
            </div>
            </div>

            <InstitutionPageActionFooter note={data.footer_note}>
              <Button
                type="button"
                variant="outline"
                className={cn(institutionActionButtonOutline, "gap-1.5")}
                disabled={reset.isPending}
                onClick={() => reset.mutate()}
              >
                <CollegeAdminRefreshCw className="size-3.5" aria-hidden />
                {data.reset_label}
              </Button>
              <Button
                type="submit"
                className={institutionActionButtonPrimary}
                disabled={save.isPending}
              >
                <CheckIcon className="size-3.5" aria-hidden />
                {data.save_label}
              </Button>
            </InstitutionPageActionFooter>
          </form>
        ) : null}
      </QueryState>
    </div>
  );
}