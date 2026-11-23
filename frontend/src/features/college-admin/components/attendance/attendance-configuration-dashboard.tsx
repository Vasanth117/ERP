"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { toast } from "sonner";

import { CheckIcon } from "@/components/icons/erp/generated/check";
import { XIcon } from "@/components/icons/erp/generated/x";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useAttendanceConfigurationPage,
  useSaveAttendanceConfiguration,
} from "@/features/college-admin/hooks/use-attendance-configuration";
import type {
  AttendanceConfigurationFieldMeta,
  AttendanceConfigurationToggleRule,
  AttendanceFieldOption,
} from "@/features/college-admin/types/attendance-configuration";
import { cn } from "@/lib/utils";

function RuleSwitch({
  rule,
  checked,
  onChange,
  disabled,
}: {
  rule: AttendanceConfigurationToggleRule;
  checked: boolean;
  onChange: (v: boolean) => void;
  disabled?: boolean;
}) {
  return (
    <div className="flex items-start justify-between gap-3 border-b border-[#f1f5f9] py-3.5 last:border-0">
      <div>
        <p className="text-[13px] font-medium text-[#111827]">{rule.label}</p>
        <p className="text-[12px] text-[#6b7280]">{rule.description}</p>
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => onChange(!checked)}
        className={cn(
          "relative h-6 w-11 shrink-0 rounded-full disabled:opacity-50",
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

function ConfigSelect({
  meta,
  value,
  options,
  onChange,
}: {
  meta: AttendanceConfigurationFieldMeta;
  value: string;
  options: AttendanceFieldOption[];
  onChange: (v: string) => void;
}) {
  const id = `attendance-config-${meta.key}`;
  return (
    <div className="space-y-1.5">
      <Label htmlFor={id} className="text-[13px] text-[#374151]">
        {meta.label}
      </Label>
      <select
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="h-9 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px] text-[#374151]"
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
}

function optionsForKey(
  key: string,
  data: {
    marking_window_options: AttendanceFieldOption[];
    correction_window_options: AttendanceFieldOption[];
    late_mark_after_options: AttendanceFieldOption[];
    session_length_options: AttendanceFieldOption[];
  },
) {
  if (key === "marking_window_key") return data.marking_window_options;
  if (key === "correction_window_key") return data.correction_window_options;
  if (key === "late_mark_after_key") return data.late_mark_after_options;
  if (key === "session_length_key") return data.session_length_options;
  return [];
}

type FormState = {
  marking_window_key: string;
  correction_window_key: string;
  late_mark_after_key: string;
  session_length_key: string;
};

export function AttendanceConfigurationDashboard() {
  const { data, isLoading, isError, error, refetch } = useAttendanceConfigurationPage();
  const save = useSaveAttendanceConfiguration();

  const [form, setForm] = useState<FormState | null>(null);
  const [toggles, setToggles] = useState<Record<string, boolean>>({});
  const [baseline, setBaseline] = useState<{ form: FormState; toggles: Record<string, boolean> } | null>(null);

  useEffect(() => {
    if (!data) return;
    const nextForm: FormState = {
      marking_window_key: data.marking_window_key,
      correction_window_key: data.correction_window_key,
      late_mark_after_key: data.late_mark_after_key,
      session_length_key: data.session_length_key,
    };
    const nextToggles: Record<string, boolean> = {};
    for (const rule of data.toggle_rules) {
      nextToggles[rule.key] = rule.enabled;
    }
    setForm(nextForm);
    setToggles(nextToggles);
    setBaseline({ form: nextForm, toggles: nextToggles });
  }, [data]);

  const handleCancel = () => {
    if (baseline) {
      setForm({ ...baseline.form });
      setToggles({ ...baseline.toggles });
    }
  };

  const handleSave = () => {
    if (!form) return;
    save.mutate(
      { ...form, toggle_rules: toggles },
      {
        onSuccess: (page) => {
          toast.success("Configuration saved");
          const nextToggles: Record<string, boolean> = {};
          for (const rule of page.toggle_rules) {
            nextToggles[rule.key] = rule.enabled;
          }
          const nextForm: FormState = {
            marking_window_key: page.marking_window_key,
            correction_window_key: page.correction_window_key,
            late_mark_after_key: page.late_mark_after_key,
            session_length_key: page.session_length_key,
          };
          setBaseline({ form: nextForm, toggles: nextToggles });
        },
        onError: (e: Error) => toast.error(e.message),
      },
    );
  };

  return (
    <div className="space-y-5" data-figma-frame="159:9831">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Attendance Configuration"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">{data?.page_subtitle ?? "—"}</p>
          {data?.rules_policies_href ? (
            <Link
              href={data.rules_policies_href}
              className="mt-2 inline-block text-[13px] font-medium text-[#245dd8] hover:underline"
            >
              {data.rules_policies_link_label} →
            </Link>
          ) : null}
        </div>
        <div className="flex shrink-0 gap-2">
          <Button
            type="button"
            variant="outline"
            className="h-9 gap-1.5 text-xs"
            disabled={!form}
            onClick={handleCancel}
          >
            <XIcon className="size-3.5" aria-hidden />
            {data?.cancel_label ?? "Cancel"}
          </Button>
          <Button
            type="button"
            className="h-9 gap-1.5 bg-[#245dd8] text-xs text-white hover:bg-[#1f4fb8]"
            disabled={save.isPending || !form}
            onClick={handleSave}
          >
            <CheckIcon className="size-3.5" aria-hidden />
            {data?.save_label ?? "Save"}
          </Button>
        </div>
      </div>

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data && form ? (
          <>
            <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_320px]">
              <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)] sm:p-6">
                <h3 className="mb-5 text-[14px] font-semibold text-[#111827]">{data.marking_section_title}</h3>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  {data.field_meta.map((meta) => (
                    <ConfigSelect
                      key={meta.key}
                      meta={meta}
                      value={form[meta.key as keyof FormState]}
                      options={optionsForKey(meta.key, data)}
                      onChange={(v) => setForm((prev) => (prev ? { ...prev, [meta.key]: v } : prev))}
                    />
                  ))}
                </div>
              </section>

              <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <h3 className="mb-1 text-[14px] font-semibold text-[#111827]">{data.behaviour_section_title}</h3>
                <div className="mt-2">
                  {data.toggle_rules.map((rule) => (
                    <RuleSwitch
                      key={rule.key}
                      rule={rule}
                      checked={Boolean(toggles[rule.key])}
                      onChange={(next) => setToggles((prev) => ({ ...prev, [rule.key]: next }))}
                    />
                  ))}
                </div>
              </section>
            </div>

          </>
        ) : null}
      </QueryState>
    </div>
  );
}