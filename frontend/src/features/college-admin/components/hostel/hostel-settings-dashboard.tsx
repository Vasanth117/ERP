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
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useHostelSettingsPage,
  useSaveHostelSettingsPage,
} from "@/features/college-admin/hooks/use-hostel-settings-page";
import type {
  HostelSettingsFormValues,
  HostelSettingsToggleRule,
} from "@/features/college-admin/types/hostel-settings-page";
import type { InstitutionFieldMeta, InstitutionFieldOption } from "@/features/college-admin/types/institution";
import { cn } from "@/lib/utils";

const RULE_FIELD_KEYS: (keyof HostelSettingsFormValues)[] = [
  "gate_closing_boys",
  "gate_closing_girls",
  "visiting_hours",
  "security_deposit",
  "outpass_approver",
  "mess_plans",
];

function metaFor(meta: InstitutionFieldMeta[], key: string) {
  return meta.find((row) => row.key === key);
}

function FieldControl({
  fieldKey,
  meta,
  options,
  watch,
  setValue,
}: {
  fieldKey: keyof HostelSettingsFormValues;
  meta?: InstitutionFieldMeta;
  options?: InstitutionFieldOption[];
  watch: ReturnType<typeof useForm<HostelSettingsFormValues>>["watch"];
  setValue: ReturnType<typeof useForm<HostelSettingsFormValues>>["setValue"];
}) {
  if (!meta) return null;
  const value = String(watch(fieldKey) ?? "");
  if (meta.field_type === "select") {
    return (
      <div>
        <Label className="text-[13px] text-[#374151]">{meta.label}</Label>
        <select
          className="mt-1.5 h-9 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px]"
          value={value}
          onChange={(e) => setValue(fieldKey, e.target.value as never, { shouldDirty: true })}
        >
          <option value="">Select</option>
          {(options ?? []).map((opt) => (
            <option key={opt.value || opt.label} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>
    );
  }
  const inputType = meta.field_type === "time" ? "time" : "text";
  return (
    <div>
      <Label className="text-[13px] text-[#374151]">{meta.label}</Label>
      <Input
        type={inputType}
        className="mt-1.5 h-9 border-[#dce3ec] text-[13px]"
        value={value}
        onChange={(e) => setValue(fieldKey, e.target.value as never, { shouldDirty: true })}
      />
    </div>
  );
}

function ToggleRow({
  rule,
  checked,
  onChange,
}: {
  rule: HostelSettingsToggleRule;
  checked: boolean;
  onChange: (next: boolean) => void;
}) {
  return (
    <div className="flex items-start justify-between gap-3 py-3.5 first:pt-1">
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

export function HostelSettingsDashboard() {
  const { data, isLoading, isError, error, refetch } = useHostelSettingsPage();
  const save = useSaveHostelSettingsPage();

  const defaults = useMemo(() => data?.form, [data?.form]);
  const form = useForm<HostelSettingsFormValues>({ defaultValues: defaults });

  useEffect(() => {
    if (defaults) form.reset(defaults);
  }, [defaults, form]);

  const toggleField = (key: keyof HostelSettingsFormValues, enabled: boolean) => {
    form.setValue(key, enabled as never, { shouldDirty: true });
  };

  return (
    <div className="space-y-5" data-figma-frame="161:6645">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Hostel Settings"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">{data?.page_subtitle ?? "Rules and timings"}</p>
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
              {data.cancel_label}
            </Button>
            <Button
              type="button"
              className={institutionActionButtonPrimary}
              disabled={save.isPending || !form.formState.isDirty}
              onClick={form.handleSubmit((values) => save.mutate(values))}
            >
              <CheckIcon className="size-3.5" aria-hidden />
              {data.save_label}
            </Button>
          </div>
        ) : null}
      </div>

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_300px]">
            <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.hostel_rules_section_title}</h3>
              </div>
              <div className="grid gap-4 px-5 py-4 sm:grid-cols-2">
                {RULE_FIELD_KEYS.map((fieldKey) => (
                  <FieldControl
                    key={fieldKey}
                    fieldKey={fieldKey}
                    meta={metaFor(data.field_meta, fieldKey)}
                    options={data.field_options[fieldKey]}
                    watch={form.watch}
                    setValue={form.setValue}
                  />
                ))}
              </div>
            </section>

            <section className="h-fit overflow-hidden rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <h3 className="mb-2 text-[14px] font-semibold text-[#111827]">{data.controls_section_title}</h3>
              <div className="divide-y divide-[#f1f5f9]">
                {data.toggle_rules.map((rule) => (
                  <ToggleRow
                    key={rule.key}
                    rule={rule}
                    checked={Boolean(form.watch(rule.key as keyof HostelSettingsFormValues))}
                    onChange={(next) => toggleField(rule.key as keyof HostelSettingsFormValues, next)}
                  />
                ))}
              </div>
            </section>
          </div>
        ) : null}
      </QueryState>
    </div>
  );
}