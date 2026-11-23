"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { onCollegeAdminMutationError } from "@/features/college-admin/context/college-admin-validation-context";
import { toast } from "sonner";

import { BookOpenIcon } from "@/components/icons/erp/generated/book-open";
import { CalendarIcon } from "@/components/icons/erp/generated/calendar";
import { CheckIcon } from "@/components/icons/erp/generated/check";
import { ChevronLeftIcon } from "@/components/icons/erp/generated/chevron-left";
import { ChevronRightIcon } from "@/components/icons/erp/generated/chevron-right";
import { FileTextIcon } from "@/components/icons/erp/generated/file-text";
import { SaveIcon } from "@/components/icons/erp/generated/save";
import { UsersIcon } from "@/components/icons/erp/generated/users";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useNewStudentRegistrationPage,
  useSaveNewStudentRegistrationDraft,
} from "@/features/college-admin/hooks/use-new-student-registration";
import type { NewStudentRegistrationFormValues } from "@/features/college-admin/types/new-student-registration";
import type { InstitutionFieldMeta } from "@/features/college-admin/types/institution";
import { cn } from "@/lib/utils";

const SUMMARY_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  application: FileTextIcon,
  programme: BookOpenIcon,
  quota: UsersIcon,
  intake: CalendarIcon,
};

function metaFor(fieldMeta: InstitutionFieldMeta[], key: string) {
  return fieldMeta.find((row) => row.key === key);
}

function FormField({ meta, children }: { meta?: InstitutionFieldMeta; children: React.ReactNode }) {
  if (!meta) return null;
  return (
    <div className="space-y-1.5" data-field-key={meta.key}>
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

function RegistrationStepper({
  steps,
  activeKey,
}: {
  steps: { key: string; label: string; step_number: number; status: string }[];
  activeKey: string;
}) {
  return (
    <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white px-4 py-4 shadow-[0_1px_2px_rgba(15,23,42,0.04)] sm:px-6">
      <div className="flex flex-wrap items-center gap-y-3 sm:flex-nowrap">
        {steps.map((wizardStep, index) => {
          const active = wizardStep.key === activeKey;
          const done = wizardStep.status === "done";
          return (
            <div key={wizardStep.key} className="flex min-w-0 flex-1 items-center last:flex-none">
              <span
                className={cn(
                  "flex size-8 shrink-0 items-center justify-center rounded-full text-[13px] font-semibold tabular-nums",
                  active && "border-2 border-[#245dd8] bg-white text-[#245dd8]",
                  !active && !done && "border border-[#e5e7eb] bg-[#f9fafb] text-[#9ca3af]",
                  done && "border-2 border-[#245dd8] bg-[#245dd8] text-white",
                )}
              >
                {done ? <CheckIcon className="size-3.5" strokeWidth={2.5} aria-hidden /> : wizardStep.step_number}
              </span>
              <span
                className={cn(
                  "ml-2 hidden truncate text-[12px] sm:inline sm:text-[13px]",
                  active ? "font-semibold text-[#111827]" : "font-medium text-[#9ca3af]",
                )}
              >
                {wizardStep.label}
              </span>
              {index < steps.length - 1 ? (
                <div className="mx-2 hidden h-px min-w-[1rem] flex-1 bg-[#e5e7eb] sm:block" aria-hidden />
              ) : null}
            </div>
          );
        })}
      </div>
    </section>
  );
}


function toPayload(values: NewStudentRegistrationFormValues): Record<string, unknown> {
  return { ...values };
}

export function NewStudentRegistrationDashboard() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const admissionIdParam = useMemo(() => searchParams.get("admission_id") ?? undefined, [searchParams]);

  const pageQuery = useNewStudentRegistrationPage(admissionIdParam);
  const saveDraft = useSaveNewStudentRegistrationDraft();

  const data = pageQuery.data;
  const defaults = data?.form;

  const form = useForm<NewStudentRegistrationFormValues>({
    values: defaults,
  });

  const [activeStep, setActiveStep] = useState("admission");

  useEffect(() => {
    if (data?.current_step_key) {
      setActiveStep(data.current_step_key);
    }
  }, [data?.current_step_key]);

  useEffect(() => {
    if (data?.admission_id && !admissionIdParam) {
      const params = new URLSearchParams(searchParams.toString());
      params.set("admission_id", data.admission_id);
      router.replace(`/college-admin/students/new-student-registration?${params.toString()}`);
    }
  }, [data?.admission_id, admissionIdParam, router, searchParams]);

  const fieldMeta = data?.field_meta ?? [];

  const handleSaveDraft = form.handleSubmit((values) => {
    if (!data) return;
    saveDraft.mutate(
      { admission_id: data.admission_id, step_key: activeStep, values: toPayload(values) },
      {
        onSuccess: () => toast.success("Draft saved"),
        onError: onCollegeAdminMutationError,
      },
    );
  });

  const handleContinue = form.handleSubmit((values) => {
    if (!data) return;
    saveDraft.mutate(
      {
        admission_id: data.admission_id,
        step_key: activeStep,
        advance: true,
        values: toPayload(values),
      },
      {
        onSuccess: (res) => {
          setActiveStep(res.current_step_key);
          toast.success("Saved — continue to the next step");
        },
        onError: onCollegeAdminMutationError,
      },
    );
  });

  const isBusy = saveDraft.isPending;

  return (
    <div className="space-y-5" data-figma-frame="158:3354">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <div className="flex items-center gap-1">
            <Link
              href={data?.back_href ?? "/college-admin/students/student-admission"}
              className="inline-flex size-8 shrink-0 items-center justify-center rounded-md text-[#374151] hover:bg-[#f3f4f6]"
              aria-label={data?.back_label ?? "Back"}
            >
              <ChevronLeftIcon className="size-5" />
            </Link>
            <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
              {data?.page_title ?? "New Student Registration"}
            </h2>
          </div>
          <p className="mt-1 pl-9 text-[14px] text-[#6b7280]">
            {data?.page_subtitle ?? "Step 2 of 6 · Student information"}
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <button
            type="button"
            disabled={!data || isBusy}
            onClick={() => void handleSaveDraft()}
            className="inline-flex h-9 items-center gap-1.5 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb] disabled:opacity-50"
          >
            <SaveIcon className="size-3.5" aria-hidden />
            {data?.save_draft_label ?? "Save draft"}
          </button>
          <button
            type="button"
            disabled={!data || isBusy}
            onClick={() => void handleContinue()}
            className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8] disabled:opacity-50"
          >
            {data?.continue_label ?? "Continue"}
            <ChevronRightIcon className="size-3.5" aria-hidden />
          </button>
        </div>
      </div>

      {data ? <RegistrationStepper steps={data.steps} activeKey={activeStep} /> : null}

      <QueryState
        isLoading={pageQuery.isLoading}
        isError={pageQuery.isError}
        error={pageQuery.error}
        onRetry={() => void pageQuery.refetch()}
      >
        {data ? (
          <>
            <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_320px]">
              <div className="space-y-5">
                {activeStep === "admission" ? (
                  <Section title="Admission details">
                    <div className="grid gap-4 sm:grid-cols-2">
                      <FormField meta={{ key: "programme_code", label: "Programme", required: true }}>
                        <select
                          className="h-9 w-full rounded-md border border-[#dce3ec] px-3 text-[13px]"
                          {...form.register("programme_code")}
                        >
                          {(data.programme_options ?? []).map((opt) => (
                            <option key={opt.value || opt.label} value={opt.value}>
                              {opt.label}
                            </option>
                          ))}
                        </select>
                      </FormField>
                      <FormField meta={{ key: "academic_year_code", label: "Academic year", required: true }}>
                        <select
                          className="h-9 w-full rounded-md border border-[#dce3ec] px-3 text-[13px]"
                          {...form.register("academic_year_code")}
                        >
                          {(data.academic_year_options ?? []).map((opt) => (
                            <option key={opt.value || opt.label} value={opt.value}>
                              {opt.label}
                            </option>
                          ))}
                        </select>
                      </FormField>
                      <FormField meta={metaFor(fieldMeta, "community")}>
                        <select
                          className="h-9 w-full rounded-md border border-[#dce3ec] px-3 text-[13px]"
                          {...form.register("community")}
                        >
                          {data.community_options.map((opt) => (
                            <option key={opt.value || opt.label} value={opt.value}>
                              {opt.label}
                            </option>
                          ))}
                        </select>
                      </FormField>
                      <FormField meta={{ key: "marks_percentage", label: "Marks / percentage", required: false }}>
                        <Input
                          className="h-9"
                          inputMode="decimal"
                          placeholder="e.g. 96.4"
                          {...form.register("marks_percentage")}
                        />
                      </FormField>
                    </div>
                  </Section>
                ) : activeStep === "student_information" ? (
                  <>
                    <Section
                      title={data.sections.find((s) => s.key === "personal_details")?.title ?? "Personal details"}
                    >
                      <div className="grid gap-4 sm:grid-cols-2">
                        <FormField meta={metaFor(fieldMeta, "full_name")}>
                          <Input className="h-9" {...form.register("full_name")} />
                        </FormField>
                        <FormField meta={metaFor(fieldMeta, "date_of_birth")}>
                          <Input className="h-9" type="date" {...form.register("date_of_birth")} />
                        </FormField>
                        <FormField meta={metaFor(fieldMeta, "gender")}>
                          <select
                            className="h-9 w-full rounded-md border border-[#dce3ec] px-3 text-[13px]"
                            {...form.register("gender")}
                          >
                            {data.gender_options.map((opt) => (
                              <option key={opt.value || opt.label} value={opt.value}>
                                {opt.label}
                              </option>
                            ))}
                          </select>
                        </FormField>
                        <FormField meta={metaFor(fieldMeta, "blood_group")}>
                          <select
                            className="h-9 w-full rounded-md border border-[#dce3ec] px-3 text-[13px]"
                            {...form.register("blood_group")}
                          >
                            {data.blood_group_options.map((opt) => (
                              <option key={opt.value || opt.label} value={opt.value}>
                                {opt.label}
                              </option>
                            ))}
                          </select>
                        </FormField>
                        <FormField meta={metaFor(fieldMeta, "mobile")}>
                          <Input className="h-9" {...form.register("mobile")} />
                        </FormField>
                        <FormField meta={metaFor(fieldMeta, "email")}>
                          <Input className="h-9" type="email" {...form.register("email")} />
                        </FormField>
                        <FormField meta={metaFor(fieldMeta, "nationality")}>
                          <select
                            className="h-9 w-full rounded-md border border-[#dce3ec] px-3 text-[13px]"
                            {...form.register("nationality")}
                          >
                            {data.nationality_options.map((opt) => (
                              <option key={opt.value || opt.label} value={opt.value}>
                                {opt.label}
                              </option>
                            ))}
                          </select>
                        </FormField>
                        <FormField meta={metaFor(fieldMeta, "community")}>
                          <select
                            className="h-9 w-full rounded-md border border-[#dce3ec] px-3 text-[13px]"
                            {...form.register("community")}
                          >
                            {data.community_options.map((opt) => (
                              <option key={opt.value || opt.label} value={opt.value}>
                                {opt.label}
                              </option>
                            ))}
                          </select>
                        </FormField>
                      </div>
                    </Section>

                    <Section
                      title={data.sections.find((s) => s.key === "guardian_details")?.title ?? "Guardian details"}
                    >
                      <div className="grid gap-4 sm:grid-cols-2">
                        <FormField meta={metaFor(fieldMeta, "guardian_name")}>
                          <Input className="h-9" {...form.register("guardian_name")} />
                        </FormField>
                        <FormField meta={metaFor(fieldMeta, "relationship")}>
                          <select
                            className="h-9 w-full rounded-md border border-[#dce3ec] px-3 text-[13px]"
                            {...form.register("relationship")}
                          >
                            {data.relationship_options.map((opt) => (
                              <option key={opt.value || opt.label} value={opt.value}>
                                {opt.label}
                              </option>
                            ))}
                          </select>
                        </FormField>
                        <FormField meta={metaFor(fieldMeta, "guardian_mobile")}>
                          <Input className="h-9" {...form.register("guardian_mobile")} />
                        </FormField>
                        <FormField meta={metaFor(fieldMeta, "occupation")}>
                          <Input className="h-9" {...form.register("occupation")} />
                        </FormField>
                      </div>
                    </Section>
                  </>
                ) : (
                  <Section title={data.steps.find((s) => s.key === activeStep)?.label ?? "Next step"}>
                    <p className="text-sm text-[#6b7280]">
                      This step will be available in a follow-up release. Use Save draft to keep your student
                      information, or go back to the Admissions list.
                    </p>
                  </Section>
                )}
              </div>

              <div className="space-y-5">
                <Section title={data.admission_summary_title}>
                  <ul className="space-y-3.5">
                    {data.admission_summary.map((row) => {
                      const Icon = SUMMARY_ICONS[row.key] ?? FileTextIcon;
                      return (
                        <li key={row.key} className="flex items-start gap-3 text-[13px]">
                          <Icon className="mt-0.5 size-4 shrink-0 text-[#9ca3af]" aria-hidden />
                          <div className="min-w-0">
                            <p className="text-[#6b7280]">{row.label}</p>
                            <p className="font-medium text-[#111827]">{row.value}</p>
                          </div>
                        </li>
                      );
                    })}
                  </ul>
                </Section>

                <Section title={data.next_steps_title}>
                  <ul className="space-y-4">
                    {data.next_steps.map((step) => (
                      <li key={step.key} className="flex gap-3">
                        <span
                          className={cn(
                            "mt-1.5 size-2 shrink-0 rounded-full",
                            step.tone === "info" ? "bg-[#245dd8]" : "bg-[#d1d5db]",
                          )}
                        />
                        <div>
                          <p className="text-[13px] font-medium text-[#111827]">{step.label}</p>
                          <p
                            className={cn(
                              "text-[11px]",
                              step.tone === "info" ? "text-[#245dd8]" : "text-[#6b7280]",
                            )}
                          >
                            {step.status_label}
                          </p>
                        </div>
                      </li>
                    ))}
                  </ul>
                </Section>
              </div>
            </div>

          </>
        ) : null}
      </QueryState>
    </div>
  );
}