"use client";

import { CollegeAdminModulePageLayout } from "@/features/college-admin/components/layout/college-admin-module-page-layout";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { onCollegeAdminMutationError } from "@/features/college-admin/context/college-admin-validation-context";
import { CollegeAdminModulePageHeading } from "@/features/college-admin/components/layout/college-admin-module-page-heading";
import { toast } from "sonner";

import { CheckIcon } from "@/components/icons/erp/generated/check";
import { XIcon } from "@/components/icons/erp/generated/x";
import { Button, buttonVariants } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useAttendanceConfigurationPage,
  useSaveAttendanceConfiguration,
} from "@/features/college-admin/hooks/use-attendance-configuration";
import { CollegeAdminPanelChromeFooter } from "@/features/college-admin/components/ui/dashboard-panel-ui";
import type {
  AttendanceConfigurationFieldMeta,
  AttendanceConfigurationPage,
  AttendanceConfigurationSummaryItem,
  AttendanceConfigurationToggleRule,
  AttendanceFieldOption,
} from "@/features/college-admin/types/attendance-configuration";
import { cn } from "@/lib/utils";

function SummaryValuePill({ label, tone }: { label: string; tone: string }) {
  const isOn = tone === "success";
  const isOff = tone === "muted";
  if (!isOn && !isOff) {
    return <span className="text-[13px] font-medium text-[#111827]">{label}</span>;
  }
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[12px] font-medium",
        isOn ? "bg-[#ecfdf5] text-[#047857]" : "bg-[#f3f4f6] text-[#6b7280]",
      )}
    >
      <span className={cn("size-1.5 rounded-full", isOn ? "bg-[#10b981]" : "bg-[#9ca3af]")} />
      {label}
    </span>
  );
}

function ConfigSummaryRow({
  item,
  expanded,
  onToggle,
}: {
  item: AttendanceConfigurationSummaryItem;
  expanded: boolean;
  onToggle: () => void;
}) {
  const hasDetail = Boolean(item.detail_description?.trim());
  return (
    <div
      className={cn(
        "border-b border-[#f1f5f9] last:border-0",
        hasDetail && "cursor-pointer hover:bg-[#fafbfc]",
      )}
    >
      <button
        type="button"
        className="flex w-full flex-col gap-1 px-0 py-3 text-left sm:flex-row sm:items-center sm:justify-between"
        onClick={hasDetail ? onToggle : undefined}
        disabled={!hasDetail}
      >
        <span className="text-[13px] font-medium text-[#374151]">{item.label}</span>
        <SummaryValuePill label={item.value_label} tone={item.value_tone ?? "default"} />
      </button>
      {expanded && hasDetail ? (
        <p className="pb-3 text-[12px] leading-relaxed text-[#6b7280]">{item.detail_description}</p>
      ) : null}
    </div>
  );
}

function ConfigSummarySection({
  title,
  items,
  expandedKey,
  onExpand,
}: {
  title: string;
  items: AttendanceConfigurationSummaryItem[];
  expandedKey: string | null;
  onExpand: (key: string) => void;
}) {
  if (!items.length) return null;
  return (
    <div>
      <h4 className="text-[12px] font-semibold uppercase tracking-wide text-[#9ca3af]">{title}</h4>
      <div className="mt-2" role="list">
        {items.map((item) => (
          <ConfigSummaryRow
            key={item.key}
            item={item}
            expanded={expandedKey === item.key}
            onToggle={() => onExpand(item.key)}
          />
        ))}
      </div>
    </div>
  );
}

function ConfigurationViewPanel({ data }: { data: AttendanceConfigurationPage }) {
  const [expandedKey, setExpandedKey] = useState<string | null>(null);
  const markingItems = data.summary_items.filter((i) => (i.section_key ?? "marking") === "marking");
  const behaviourItems = data.summary_items.filter((i) => i.section_key === "behaviour");

  return (
    <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_320px]">
      <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
        <div className="border-b border-[#f1f5f9] px-5 py-3.5">
          <h3 className="text-[14px] font-semibold text-[#111827]">
            {data.current_settings_section_title ?? "Current configuration"}
          </h3>
          <p className="mt-1 text-[13px] text-[#6b7280]">{data.view_settings_description}</p>
        </div>
        <div className="space-y-6 px-5 py-5 sm:px-6">
          <ConfigSummarySection
            title={data.marking_section_title}
            items={markingItems}
            expandedKey={expandedKey}
            onExpand={(key) => setExpandedKey((cur) => (cur === key ? null : key))}
          />
          <ConfigSummarySection
            title={data.behaviour_section_title}
            items={behaviourItems}
            expandedKey={expandedKey}
            onExpand={(key) => setExpandedKey((cur) => (cur === key ? null : key))}
          />
        </div>
        <CollegeAdminPanelChromeFooter>
          <span>{data.footer_disclaimer}</span>
          <span className="shrink-0 tabular-nums">{data.footer_snapshot_label}</span>
        </CollegeAdminPanelChromeFooter>
      </section>

      <aside className="flex flex-col gap-5">
        <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
          <div className="border-b border-[#f1f5f9] px-5 py-3.5">
            <h3 className="text-[14px] font-semibold text-[#111827]">
              {data.related_policies_section_title ?? "Institutional policies"}
            </h3>
            <p className="mt-1 text-[12px] text-[#6b7280]">
              {data.related_policies_description ??
                "Preview of policy rows linked to marking and eligibility."}
            </p>
          </div>
          {data.policy_preview_rows?.length ? (
            <ul className="divide-y divide-[#f1f5f9] px-5">
              {data.policy_preview_rows.map((row) => (
                <li key={row.row_key} className="py-3">
                  <p className="text-[13px] font-semibold text-[#111827]">{row.policy_title}</p>
                  <p className="mt-0.5 text-[13px] text-[#245dd8]">{row.value_label}</p>
                  <p className="mt-0.5 text-[12px] text-[#6b7280]">{row.applies_to_label}</p>
                </li>
              ))}
            </ul>
          ) : (
            <p className="px-5 py-6 text-[13px] text-[#6b7280]">No policies in catalog yet.</p>
          )}
          <CollegeAdminPanelChromeFooter className="flex-col items-stretch gap-2 sm:flex-row sm:items-center">
            <Link
              href={data.rules_policies_href}
              className={cn(buttonVariants({ variant: "outline" }), "h-8 w-full justify-center text-xs sm:w-auto")}
            >
              {data.rules_policies_link_label}
            </Link>
            {data.reports_href ? (
              <Link
                href={data.reports_href}
                className={cn(buttonVariants({ variant: "outline" }), "h-8 w-full justify-center text-xs sm:w-auto")}
              >
                {data.reports_link_label}
              </Link>
            ) : null}
          </CollegeAdminPanelChromeFooter>
        </section>
      </aside>
    </div>
  );
}

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
  const searchParams = useSearchParams();
  const { data, isLoading, isError, error, refetch } = useAttendanceConfigurationPage();
  const save = useSaveAttendanceConfiguration();

  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState<FormState | null>(null);
  const [toggles, setToggles] = useState<Record<string, boolean>>({});
  const [baseline, setBaseline] = useState<{ form: FormState; toggles: Record<string, boolean> } | null>(null);

  useEffect(() => {
    if (searchParams?.get("edit") === "1") {
      setEditing(true);
    }
  }, [searchParams]);

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

  const handleCancelEdit = () => {
    if (baseline) {
      setForm({ ...baseline.form });
      setToggles({ ...baseline.toggles });
    }
    setEditing(false);
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
          setEditing(false);
        },
        onError: onCollegeAdminMutationError,
      },
    );
  };

  return (
    <CollegeAdminModulePageLayout figmaFrame="159:9831">
      <CollegeAdminModulePageHeading title={data?.page_title ?? "Attendance Configuration"} subtitle={data?.page_subtitle ?? "—"} actions={<>{editing ? (
            <>
              <Button
                type="button"
                variant="outline"
                className="h-9 gap-1.5 text-xs"
                disabled={!form}
                onClick={handleCancelEdit}
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
                {data?.save_label ?? "Save changes"}
              </Button>
            </>
          ) : (
            <>
              <Button
                type="button"
                variant="outline"
                className="h-9 text-xs"
                disabled={!data}
                onClick={() => setEditing(true)}
              >
                {data?.edit_settings_label ?? "Edit configuration"}
              </Button>
              {data?.rules_policies_href ? (
                <Link
                  href={data.rules_policies_href}
                  className={cn(
                    buttonVariants({ variant: "default" }),
                    "h-9 bg-[#245dd8] text-xs text-white hover:bg-[#1f4fb8]",
                  )}
                >
                  {data.rules_policies_link_label ?? "Rules & policies"}
                </Link>
              ) : null}
            </>
          )}</>} />

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data && !editing ? <ConfigurationViewPanel data={data} /> : null}

        {data && form && editing ? (
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
        ) : null}

        {data && editing ? (
          <CollegeAdminPanelChromeFooter className="rounded-xl border border-[#e8ecf2] bg-[#fafbfc]">
            <span>{data.footer_disclaimer}</span>
            <span className="shrink-0 tabular-nums">{data.footer_snapshot_label}</span>
          </CollegeAdminPanelChromeFooter>
        ) : null}
      </QueryState>
    </CollegeAdminModulePageLayout>
  );
}