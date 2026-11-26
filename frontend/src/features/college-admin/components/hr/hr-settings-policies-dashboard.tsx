"use client";

import { useEffect, useMemo } from "react";
import { useForm } from "react-hook-form";

import { CheckIcon } from "@/components/icons/erp/generated/check";
import { XIcon } from "@/components/icons/erp/generated/x";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  institutionActionButtonOutline,
  institutionActionButtonPrimary,
} from "@/features/college-admin/components/institution/institution-page-action-footer";
import { HrRecruitmentSubNav } from "@/features/college-admin/components/hr/hr-recruitment-sub-nav";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { onCollegeAdminMutationError } from "@/features/college-admin/context/college-admin-validation-context";
import {
  useHrSettingsPoliciesPage,
  useSaveHrSettingsPoliciesPage,
} from "@/features/college-admin/hooks/use-hr-reports-settings";
import type {
  HrSettingsPoliciesFormValues,
  HrSettingsPoliciesPage,
  HrSettingsPoliciesToggleRule,
} from "@/features/college-admin/types/hr-reports-settings";
import type { HrRecruitmentSubNavItem } from "@/features/college-admin/types/hr-recruitment";
import type { InstitutionFieldMeta, InstitutionFieldOption } from "@/features/college-admin/types/institution";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

const DEFAULT_SUB_NAV: HrRecruitmentSubNavItem[] = [
  { key: "hr-reports", label: "HR reports", href: "/college-admin/hr/hr-reports" },
  { key: "settings-policies", label: "HR settings & policies", href: "/college-admin/hr/hr-settings-policies" },
];

const POLICY_FIELD_KEYS: (keyof HrSettingsPoliciesFormValues)[] = [
  "working_week",
  "earned_leave_per_year",
  "leave_approver",
  "casual_leave_per_year",
  "probation_period_months",
  "payroll_cutoff_day",
];

function metaFor(meta: InstitutionFieldMeta[], key: string) {
  return meta.find((row) => row.key === key);
}

function FieldControl({
  fieldKey,
  meta,
  options,
  register,
  watch,
  setValue,
}: {
  fieldKey: keyof HrSettingsPoliciesFormValues;
  meta?: InstitutionFieldMeta;
  options?: InstitutionFieldOption[];
  register: ReturnType<typeof useForm<HrSettingsPoliciesFormValues>>["register"];
  watch: ReturnType<typeof useForm<HrSettingsPoliciesFormValues>>["watch"];
  setValue: ReturnType<typeof useForm<HrSettingsPoliciesFormValues>>["setValue"];
}) {
  if (!meta) return null;
  const isSelect = meta.field_type === "select" && options?.length;
  return (
    <div>
      <Label className="text-[13px] text-[#374151]">
        {meta.label}
        {meta.required ? <span className="text-[#dc2626]"> *</span> : null}
      </Label>
      {isSelect ? (
        <select
          className="mt-1.5 h-9 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px]"
          value={String(watch(fieldKey) ?? "")}
          onChange={(e) => setValue(fieldKey, e.target.value as never, { shouldDirty: true })}
        >
          {options.map((opt) => (
            <option key={opt.value || opt.label} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      ) : (
        <Input className="mt-1.5 h-9 text-[13px]" {...register(fieldKey)} />
      )}
    </div>
  );
}

function ToggleRow({
  rule,
  checked,
  onChange,
}: {
  rule: HrSettingsPoliciesToggleRule;
  checked: boolean;
  onChange: (next: boolean) => void;
}) {
  return (
    <div className="flex items-start justify-between gap-3 border-b border-[#f1f5f9] py-3.5 last:border-0">
      <div>
        <p className="text-[13px] font-medium text-[#111827]">{rule.label}</p>
        {rule.badge_label ? (
          <p className="text-[11px] text-[#6b7280]">{rule.badge_label}</p>
        ) : rule.description ? (
          <p className="text-[12px] text-[#6b7280]">{rule.description}</p>
        ) : null}
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

function mergeView(data: HrSettingsPoliciesPage | undefined) {
  return {
    page_title: data?.page_title ?? "HR Settings & Policies",
    page_subtitle: data?.page_subtitle ?? "Leave, attendance and payroll policies",
    cancel_label: data?.cancel_label ?? "Cancel",
    save_label: data?.save_label ?? "Save",
    policies_section_title: data?.policies_section_title ?? "Policies",
    controls_section_title: data?.controls_section_title ?? "Controls",
    sub_nav: data?.sub_nav?.length ? data.sub_nav : DEFAULT_SUB_NAV,
    field_meta: data?.field_meta ?? [],
    field_options: data?.field_options ?? {},
    toggle_rules: data?.toggle_rules ?? [],
    footer_disclaimer: data?.footer_disclaimer ?? "",
    footer_snapshot_label: data?.footer_snapshot_label ?? "",
  };
}

export function HrSettingsPoliciesDashboard() {
  const { data, isLoading, isError, error, refetch } = useHrSettingsPoliciesPage();
  const view = useMemo(() => mergeView(data), [data]);
  const save = useSaveHrSettingsPoliciesPage();

  const form = useForm<HrSettingsPoliciesFormValues>();

  useEffect(() => {
    if (data?.form) form.reset(data.form);
  }, [data?.form, form]);

  const toggleField = (key: keyof HrSettingsPoliciesFormValues, enabled: boolean) => {
    form.setValue(key, enabled as never, { shouldDirty: true });
  };

  return (
    <div className="space-y-5" data-figma-frame="160:11270">
      <HrRecruitmentSubNav items={view.sub_nav} />

      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">{view.page_title}</h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">{view.page_subtitle}</p>
        </div>
        {data ? (
          <div className="flex shrink-0 flex-wrap items-center gap-2">
            <Button
              type="button"
              variant="outline"
              className={institutionActionButtonOutline}
              disabled={save.isPending}
              onClick={() => form.reset(data.form)}
            >
              <XIcon className="mr-1.5 size-3.5" aria-hidden />
              {view.cancel_label}
            </Button>
            <Button
              type="button"
              className={institutionActionButtonPrimary}
              disabled={save.isPending || !form.formState.isDirty}
              onClick={form.handleSubmit((values) =>
                save.mutate(values, {
                  onSuccess: () => toast.success("Settings saved"),
                  onError: onCollegeAdminMutationError,
                }),
              )}
            >
              <CheckIcon className="size-3.5" aria-hidden />
              {view.save_label}
            </Button>
          </div>
        ) : null}
      </div>

      {isLoading ? <p className="text-[12px] text-[#9ca3af]">Loading settings…</p> : null}

      {isError ? <QueryState isError={isError} error={error} onRetry={() => void refetch()} /> : null}

      {!isError && data ? (
        <>
          <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_300px]">
            <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                <h3 className="text-[14px] font-semibold text-[#111827]">{view.policies_section_title}</h3>
              </div>
              <div className="grid gap-4 px-5 py-4 sm:grid-cols-2">
                {POLICY_FIELD_KEYS.map((fieldKey) => (
                  <FieldControl
                    key={fieldKey}
                    fieldKey={fieldKey}
                    meta={metaFor(view.field_meta, fieldKey)}
                    options={view.field_options[fieldKey]}
                    register={form.register}
                    watch={form.watch}
                    setValue={form.setValue}
                  />
                ))}
              </div>
            </section>

            <aside className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                <h3 className="text-[14px] font-semibold text-[#111827]">{view.controls_section_title}</h3>
              </div>
              <div className="px-5 pb-2">
                {view.toggle_rules.map((rule) => (
                  <ToggleRow
                    key={rule.key}
                    rule={rule}
                    checked={Boolean(form.watch(rule.key))}
                    onChange={(next) => toggleField(rule.key, next)}
                  />
                ))}
              </div>
            </aside>
          </div>

          <footer className="flex flex-col gap-1 text-[11px] text-[#9ca3af] sm:flex-row sm:items-center sm:justify-between">
            <p>{view.footer_disclaimer}</p>
            {view.footer_snapshot_label ? <p>{view.footer_snapshot_label}</p> : null}
          </footer>
        </>
      ) : null}
    </div>
  );
}