"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

import { useExaminationWorkflowContinue } from "@/features/college-admin/components/examinations/examination-creation-workflow-header";
import { ExaminationWorkflowOrPageHeading } from "@/features/college-admin/components/examinations/examination-workflow-or-page-heading";
import { useExaminationCreationFlowOptional } from "@/features/college-admin/context/examination-creation-flow-context";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { onCollegeAdminMutationError } from "@/features/college-admin/context/college-admin-validation-context";
import {
  useExaminationConfigurationPage,
  useSaveExaminationConfiguration,
} from "@/features/college-admin/hooks/use-examination-configuration";
import { useExaminationCreationSessionId } from "@/features/college-admin/hooks/use-examination-creation-flow";
import type {
  ExaminationSetupFieldMeta,
  ExaminationSetupFormValues,
  ExaminationSetupToggleRule,
} from "@/features/college-admin/types/examination-configuration";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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

const CREATION_SETUP_FIELD_KEYS = new Set([
  "session_name",
  "examination_type",
  "academic_year_label",
  "semester_label",
  "examination_start_at",
  "examination_end_at",
  "result_target_at",
]);

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
  const sessionId = useExaminationCreationSessionId();
  const creationFlow = useExaminationCreationFlowOptional();
  const continueTo = useExaminationWorkflowContinue();
  const mode = searchParams.get("mode") ?? undefined;
  const inCreationModal = Boolean(creationFlow?.isModalOpen);

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

  const persist = async (advance: boolean) => {
    if (!form || !data) return;
    try {
      const result = await save.mutateAsync({
        session_id: data.session_id,
        form,
        toggle_rules: toggles,
        advance_workflow: advance,
      });
      if (result.session_id) {
        creationFlow?.setSessionId(result.session_id);
        if (!inCreationModal && !sessionId) {
          router.replace(`/college-admin/examinations/examination-configuration?session_id=${result.session_id}`);
        }
      }
      if (advance) {
        if (!result.continue_href) {
          toast.error("Unable to continue — save the draft first.");
          return;
        }
        toast.success(
          inCreationModal
            ? "Examination saved for this year and semester — timetable prepared for all programmes."
            : "Step saved — continue to next stage",
        );
        continueTo(result.continue_href);
      } else {
        toast.success(
          inCreationModal && result.session_id
            ? "Draft saved — assessment pattern and timetable prepared."
            : "Draft saved",
        );
      }
    } catch (e) {
      onCollegeAdminMutationError(e as Error & { details?: unknown });
    }
  };

  const busy = save.isPending;
  const controlsDisabled = isLoading || !form || !data;

  return (
    <div className="space-y-5" data-figma-frame="159:11453">
      <ExaminationWorkflowOrPageHeading
        pageTitle={data?.page_title ?? "Examination Configuration"}
        pageSubtitle={data?.page_subtitle ?? "Step 1 of 6 · Create examination"}
        backHref={data?.back_href ?? "/college-admin/examinations/examination-session-management"}
        saveDraftLabel={data?.save_draft_label}
        continueLabel={data?.continue_label}
        workflowSteps={inCreationModal ? data?.workflow_steps : undefined}
        sessionId={data?.session_id ?? sessionId}
        busy={busy}
        controlsDisabled={controlsDisabled}
        continueEnabled={data?.continue_enabled ?? true}
        onSaveDraft={() => void persist(false)}
        onContinue={() => void persist(true)}
      />

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data && form ? (
          <div className={cn("grid grid-cols-1 gap-5", !inCreationModal && "xl:grid-cols-[1fr_320px]")}>
            <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)] sm:p-6">
              <h3 className="mb-5 text-[14px] font-semibold text-[#111827]">{data.setup_section_title}</h3>
              {inCreationModal ? (
                <p className="mb-4 text-[12px] text-[#6b7280]">
                  Scope applies to every programme in the selected academic year and semester. Per-student exam
                  registration is handled separately, not during this setup.
                </p>
              ) : null}
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                {(inCreationModal
                  ? data.field_meta.filter((meta) => CREATION_SETUP_FIELD_KEYS.has(meta.key))
                  : data.field_meta
                ).map((meta) => (
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

            {!inCreationModal ? (
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
            ) : null}
          </div>
        ) : null}
      </QueryState>
    </div>
  );
}