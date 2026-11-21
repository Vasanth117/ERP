"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

import { ChevronRightIcon } from "@/components/icons/erp/generated/chevron-right";
import { CollegeAdminDownload, getCollegeAdminErpIcon, resolveCollegeAdminIconSlug } from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useExaminationConfigurationPage,
  useSaveExaminationConfiguration,
} from "@/features/college-admin/hooks/use-examination-configuration";
import type {
  ExaminationSetupFieldMeta,
  ExaminationSetupFormValues,
  ExaminationSetupToggleRule,
} from "@/features/college-admin/types/examination-configuration";
import { cn } from "@/lib/utils";

function RuleSwitch({
  rule,
  checked,
  onChange,
}: {
  rule: ExaminationSetupToggleRule;
  checked: boolean;
  onChange: (v: boolean) => void;
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
        onClick={() => onChange(!checked)}
        className={cn("relative h-6 w-11 shrink-0 rounded-full", checked ? "bg-[#245dd8]" : "bg-[#d1d5db]")}
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

function SetupField({
  meta,
  value,
  options,
  onChange,
}: {
  meta: ExaminationSetupFieldMeta;
  value: string;
  options?: { value: string; label: string }[];
  onChange: (v: string) => void;
}) {
  const id = `exam-setup-${meta.key}`;
  if (meta.field_type === "select" && options?.length) {
    return (
      <div className="space-y-1.5">
        <Label htmlFor={id} className="text-[13px] text-[#374151]">
          {meta.label}
          {meta.required ? <span className="text-[#dc2626]"> *</span> : null}
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
  if (meta.field_type === "date") {
    return (
      <div className="space-y-1.5">
        <Label htmlFor={id} className="text-[13px] text-[#374151]">
          {meta.label}
          {meta.required ? <span className="text-[#dc2626]"> *</span> : null}
        </Label>
        <Input
          id={id}
          type="date"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="h-9 border-[#dce3ec] text-[13px]"
        />
      </div>
    );
  }
  return (
    <div className="space-y-1.5">
      <Label htmlFor={id} className="text-[13px] text-[#374151]">
        {meta.label}
        {meta.required ? <span className="text-[#dc2626]"> *</span> : null}
      </Label>
      <Input
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="h-9 border-[#dce3ec] text-[13px]"
      />
    </div>
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

function optionsForField(
  key: string,
  data: {
    type_options: { value: string; label: string }[];
    academic_year_options: { value: string; label: string }[];
    semester_options: { value: string; label: string }[];
  },
) {
  if (key === "examination_type") return data.type_options;
  if (key === "academic_year_label") return data.academic_year_options;
  if (key === "semester_label") return data.semester_options;
  return undefined;
}

export function ExaminationConfigurationDashboard() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const sessionId = searchParams.get("session_id") ?? undefined;
  const mode = searchParams.get("mode") ?? undefined;

  const query = useMemo(
    () => ({ session_id: sessionId, mode: sessionId ? undefined : mode }),
    [sessionId, mode],
  );

  const { data, isLoading, isError, error, refetch } = useExaminationConfigurationPage(query);
  const save = useSaveExaminationConfiguration();

  const [form, setForm] = useState<ExaminationSetupFormValues | null>(null);
  const [toggles, setToggles] = useState<Record<string, boolean>>({});

  useEffect(() => {
    if (!data) return;
    setForm({ ...data.form });
    const next: Record<string, boolean> = {};
    for (const rule of data.toggle_rules) {
      next[rule.key] = rule.enabled;
    }
    setToggles(next);
  }, [data]);

  const BackIcon = getCollegeAdminErpIcon(resolveCollegeAdminIconSlug("arrow-left"));

  const persist = async (advance: boolean) => {
    if (!form || !data) return;
    try {
      const result = await save.mutateAsync({
        session_id: data.session_id,
        form,
        toggle_rules: toggles,
        advance_workflow: advance,
      });
      if (result.session_id && data.is_new) {
        router.replace(`/college-admin/examinations/examination-configuration?session_id=${result.session_id}`);
      }
      if (advance) {
        router.push(result.continue_href);
      } else {
        toast.success("Draft saved");
      }
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Save failed");
    }
  };

  return (
    <div className="space-y-5" data-figma-frame="159:11453">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="flex gap-3">
          <Link
            href={data?.back_href ?? "/college-admin/examinations/examination-session-management"}
            className="mt-1 flex size-9 shrink-0 items-center justify-center rounded-md border border-[#dce3ec] text-[#6b7280] hover:bg-[#f9fafb]"
            aria-label="Back"
          >
            {BackIcon ? <BackIcon className="size-4" /> : "←"}
          </Link>
          <div>
            <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
              {data?.page_title ?? "Examination Configuration"}
            </h2>
            <p className="mt-1 text-[14px] text-[#6b7280]">{data?.page_subtitle ?? "—"}</p>
          </div>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <Button
            type="button"
            variant="outline"
            className="h-9 gap-1.5 border-[#dce3ec] text-xs font-medium"
            disabled={save.isPending || !form}
            onClick={() => void persist(false)}
          >
            <CollegeAdminDownload className="size-3.5" />
            {data?.save_draft_label ?? "Save draft"}
          </Button>
          <Button
            type="button"
            className="h-9 gap-1.5 bg-[#245dd8] text-xs font-medium hover:bg-[#1f4fb8]"
            disabled={save.isPending || !form}
            onClick={() => void persist(true)}
          >
            {data?.continue_label ?? "Continue"}
            <ChevronRightIcon className="size-3.5" aria-hidden />
          </Button>
        </div>
      </div>

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data && form ? (
          <>
            <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_320px]">
              <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)] sm:p-6">
                <h3 className="mb-5 text-[14px] font-semibold text-[#111827]">{data.setup_section_title}</h3>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  {data.field_meta.map((meta) => (
                    <SetupField
                      key={meta.key}
                      meta={meta}
                      value={form[meta.key]}
                      options={optionsForField(meta.key, data)}
                      onChange={(v) => setForm((prev) => (prev ? { ...prev, [meta.key]: v } : prev))}
                    />
                  ))}
                </div>
              </section>

              <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <h3 className="mb-1 text-[14px] font-semibold text-[#111827]">{data.rules_section_title}</h3>
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

            <footer className="flex flex-col gap-2 border-t border-[#e8ecf2] pt-4 text-[11px] text-[#9ca3af] sm:flex-row sm:items-center sm:justify-between">
              <p>{data.footer_disclaimer}</p>
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