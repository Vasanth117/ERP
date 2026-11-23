"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { CheckIcon } from "@/components/icons/erp/generated/check";
import { ChevronLeftIcon } from "@/components/icons/erp/generated/chevron-left";
import { SendHorizontalIcon } from "@/components/icons/erp/generated/send-horizontal";
import { XIcon } from "@/components/icons/erp/generated/x";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { uploadCreateNewUserFile } from "@/features/college-admin/api/users";
import {
  useCreateNewUserPage,
  useSaveCreateNewUserDraft,
  useSubmitCreateNewUser,
  useValidateCreateNewUser,
} from "@/features/college-admin/hooks/use-create-new-user";
import type {
  CreateNewUserFormValues,
  CreateNewUserValidationCheck,
} from "@/features/college-admin/types/create-new-user";
import type { InstitutionFieldMeta } from "@/features/college-admin/types/institution";
import { cn } from "@/lib/utils";

type StepKey = "personal" | "role_access" | "review";

const DEFAULT_WIZARD_STEPS = [
  { key: "personal", label: "Personal details", step_number: 1 },
  { key: "role_access", label: "Role & access", step_number: 2 },
  { key: "review", label: "Review & Invite", step_number: 3 },
] as const;

function metaFor(fieldMeta: InstitutionFieldMeta[], key: string) {
  return fieldMeta.find((row) => row.key === key);
}

function FormField({ meta, children }: { meta?: InstitutionFieldMeta; children: React.ReactNode }) {
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

function ValidationBadge({ check }: { check: CreateNewUserValidationCheck }) {
  const tone: Record<string, string> = {
    success: "bg-[#ecfdf5] text-[#047857]",
    error: "bg-[#fef2f2] text-[#b91c1c]",
    muted: "bg-[#f3f4f6] text-[#6b7280]",
  };
  const dot: Record<string, string> = {
    success: "bg-[#10b981]",
    error: "bg-[#ef4444]",
    muted: "bg-[#9ca3af]",
  };
  const key = check.tone in tone ? check.tone : "muted";
  return (
    <span className={cn("inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium", tone[key])}>
      <span className={cn("size-1.5 rounded-full", dot[key])} />
      {check.status_label}
    </span>
  );
}

function toPayload(values: CreateNewUserFormValues): Record<string, unknown> {
  return { ...values };
}

function CreateUserStepper({
  steps,
  activeKey,
  activeIndex,
  onSelect,
}: {
  steps: { key: string; label: string; step_number: number }[];
  activeKey: string;
  activeIndex: number;
  onSelect: (key: StepKey) => void;
}) {
  return (
    <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white px-4 py-4 shadow-[0_1px_2px_rgba(15,23,42,0.04)] sm:px-8">
      <div className="flex items-center">
        {steps.map((wizardStep, index) => {
          const active = wizardStep.key === activeKey;
          const done = index < activeIndex;
          return (
            <div key={wizardStep.key} className="flex min-w-0 flex-1 items-center last:flex-none">
              <button
                type="button"
                onClick={() => onSelect(wizardStep.key as StepKey)}
                className="flex min-w-0 items-center gap-2.5 text-left outline-none focus-visible:ring-2 focus-visible:ring-[#245dd8]/40"
              >
                <span
                  className={cn(
                    "flex size-8 shrink-0 items-center justify-center rounded-full text-[13px] font-semibold tabular-nums",
                    active && "border-2 border-[#245dd8] bg-white text-[#245dd8]",
                    !active && !done && "border border-[#e5e7eb] bg-[#f9fafb] text-[#9ca3af]",
                    done && !active && "border-2 border-[#245dd8] bg-[#245dd8] text-white",
                  )}
                >
                  {done ? <CheckIcon className="size-3.5" strokeWidth={2.5} aria-hidden /> : wizardStep.step_number}
                </span>
                <span
                  className={cn(
                    "truncate text-[13px] sm:text-[14px]",
                    active ? "font-semibold text-[#111827]" : "font-medium text-[#9ca3af]",
                  )}
                >
                  {wizardStep.label}
                </span>
              </button>
              {index < steps.length - 1 ? (
                <div className="mx-3 hidden h-px min-w-[1.5rem] flex-1 bg-[#e5e7eb] sm:block" aria-hidden />
              ) : null}
            </div>
          );
        })}
      </div>
    </section>
  );
}

export function CreateNewUserDashboard() {
  const router = useRouter();
  const pageQuery = useCreateNewUserPage();
  const saveDraft = useSaveCreateNewUserDraft();
  const validate = useValidateCreateNewUser();
  const submit = useSubmitCreateNewUser();

  const [step, setStep] = useState<StepKey>("personal");
  const [checks, setChecks] = useState<CreateNewUserValidationCheck[]>([]);
  const [reviewLines, setReviewLines] = useState(pageQuery.data?.review_lines ?? []);
  const [confirmPassword, setConfirmPassword] = useState("");
  const [uploadingKind, setUploadingKind] = useState<string | null>(null);

  const defaults = useMemo(
    () => pageQuery.data?.form,
    [pageQuery.data?.form],
  );

  const form = useForm<CreateNewUserFormValues>({
    values: defaults,
  });

  const data = pageQuery.data;
  const fieldMeta = data?.field_meta ?? [];
  const studentMeta = data?.student_field_meta ?? [];
  const staffMeta = data?.staff_field_meta ?? [];
  const documentMeta = data?.document_field_meta ?? [];
  const watched = form.watch();
  const sendInvite = Boolean(watched.send_invitation_email);
  const isStudent = watched.user_type === "student";

  const handleProvisioningUpload = useCallback(
    async (
      kind: "profile_photo" | "identity_document" | "supporting_document",
      field: "profile_photo_ref" | "identity_document_ref" | "supporting_document_ref",
      file: File | undefined,
    ) => {
      if (!file) return;
      setUploadingKind(kind);
      try {
        const res = await uploadCreateNewUserFile(kind, file);
        form.setValue(field, res.file_id, { shouldDirty: true });
        toast.success(`${res.file_name} uploaded`);
      } catch (e) {
        toast.error(e instanceof Error ? e.message : "Upload failed");
      } finally {
        setUploadingKind(null);
      }
    },
    [form],
  );

  useEffect(() => {
    if (data?.current_step_key && ["personal", "role_access", "review"].includes(data.current_step_key)) {
      setStep(data.current_step_key as StepKey);
    }
  }, [data?.current_step_key]);

  useEffect(() => {
    if (data?.validation_checks) {
      setChecks(data.validation_checks);
    }
    if (data?.review_lines) {
      setReviewLines(data.review_lines);
    }
  }, [data?.validation_checks, data?.review_lines]);

  const runValidate = useCallback(
    (values: CreateNewUserFormValues) => {
      validate.mutate(toPayload(values), {
        onSuccess: (res) => {
          setChecks(res.validation_checks);
          setReviewLines(res.review_lines);
        },
      });
    },
    [validate],
  );

  useEffect(() => {
    const t = window.setTimeout(() => runValidate(watched), 400);
    return () => window.clearTimeout(t);
  }, [watched, runValidate]);

  const stepIndex = data?.steps.findIndex((s) => s.key === step) ?? 0;
  const nextStep = data?.steps[stepIndex + 1];

  const designationOptions =
    watched.user_type === "student"
      ? [{ value: "student", label: "Student" }]
      : data?.designation_options ?? [];

  const handleSaveDraft = form.handleSubmit((values) => {
    saveDraft.mutate(
      { step_key: step, values: toPayload(values) },
      { onSuccess: () => toast.success("Draft saved") },
    );
  });

  const handleSubmitInvite = form.handleSubmit((values) => {
    if (!values.send_invitation_email) {
      if (values.initial_password.length < 8) {
        toast.error("Password must be at least 8 characters");
        return;
      }
      if (values.initial_password !== confirmPassword) {
        toast.error("Password and confirmation do not match");
        return;
      }
    }
    submit.mutate(toPayload(values), {
      onSuccess: (res) => {
        toast.success(res.message);
        if (res.detail_href) {
          router.push(res.detail_href);
        } else {
          const email = encodeURIComponent(values.official_email.trim());
          router.push(email ? `/college-admin/users/all-users-list?search=${email}` : "/college-admin/users/all-users-list");
        }
      },
      onError: (e: Error) => toast.error(e.message),
    });
  });

  const goNext = form.handleSubmit((values) => {
    if (!nextStep) return;
    saveDraft.mutate(
      { step_key: nextStep.key, values: toPayload(values) },
      {
        onSuccess: () => {
          setStep(nextStep.key as StepKey);
          runValidate(values);
        },
      },
    );
  });

  const isBusy = saveDraft.isPending || submit.isPending;

  return (
    <div className="space-y-5" data-figma-frame="69:125683">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <div className="flex items-center gap-1">
            <Link
              href={data?.cancel_href ?? "/college-admin/users/user-management-dashboard"}
              className="inline-flex size-8 shrink-0 items-center justify-center rounded-md text-[#374151] hover:bg-[#f3f4f6]"
              aria-label="Back"
            >
              <ChevronLeftIcon className="size-5" />
            </Link>
            <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
              {data?.page_title ?? "Create New User"}
            </h2>
          </div>
          <p className="mt-1 pl-9 text-[14px] text-[#6b7280]">{data?.page_subtitle}</p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <Link
            href={data?.cancel_href ?? "/college-admin/users/user-management-dashboard"}
            className="inline-flex h-9 items-center gap-1.5 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb]"
          >
            <XIcon className="size-3.5" aria-hidden />
            {data?.cancel_label ?? "Cancel"}
          </Link>
          <button
            type="button"
            disabled={!data || isBusy}
            onClick={() => void handleSubmitInvite()}
            className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8] disabled:opacity-50"
          >
            <SendHorizontalIcon className="size-3.5" aria-hidden />
            {data?.create_invite_label ?? "Create & send invite"}
          </button>
        </div>
      </div>

      <CreateUserStepper
        steps={data?.steps ?? [...DEFAULT_WIZARD_STEPS]}
        activeKey={step}
        activeIndex={data ? stepIndex : 0}
        onSelect={setStep}
      />

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
                {step === "personal" ? (
                  <>
                    <Section title={data.sections.find((s) => s.key === "personal_details")?.title ?? "Personal details"}>
                      <div className="grid gap-4 sm:grid-cols-2">
                        <FormField meta={metaFor(fieldMeta, "first_name")}>
                          <Input className="h-9" {...form.register("first_name")} />
                        </FormField>
                        <FormField meta={metaFor(fieldMeta, "last_name")}>
                          <Input className="h-9" {...form.register("last_name")} />
                        </FormField>
                        <FormField meta={metaFor(fieldMeta, "official_email")}>
                          <Input className="h-9" type="email" {...form.register("official_email")} />
                        </FormField>
                        <FormField meta={metaFor(fieldMeta, "mobile_number")}>
                          <Input className="h-9" {...form.register("mobile_number")} />
                        </FormField>
                        <FormField meta={metaFor(fieldMeta, "public_id")}>
                          <Input className="h-9" {...form.register("public_id")} />
                        </FormField>
                        <FormField meta={metaFor(fieldMeta, "joining_date")}>
                          <Input className="h-9" type="date" {...form.register("joining_date")} />
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
                        <FormField meta={metaFor(fieldMeta, "date_of_birth")}>
                          <Input className="h-9" type="date" {...form.register("date_of_birth")} />
                        </FormField>
                      </div>
                    </Section>

                    <Section title={data.sections.find((s) => s.key === "account_type")?.title ?? "Account type"}>
                      <FormField meta={metaFor(fieldMeta, "user_type")}>
                        <div className="flex flex-wrap gap-4">
                          {data.user_type_options.map((opt) => (
                            <label key={opt.value} className="inline-flex items-center gap-2 text-[13px]">
                              <input
                                type="radio"
                                value={opt.value}
                                className="accent-[#245dd8]"
                                {...form.register("user_type")}
                              />
                              {opt.label}
                            </label>
                          ))}
                        </div>
                      </FormField>
                      <div className="mt-4 grid gap-4 sm:grid-cols-2">
                        <FormField meta={metaFor(fieldMeta, "department_id")}>
                          <select
                            className="h-9 w-full rounded-md border border-[#dce3ec] px-3 text-[13px]"
                            {...form.register("department_id")}
                          >
                            {data.department_options.map((opt) => (
                              <option key={opt.value || opt.label} value={opt.value}>
                                {opt.label}
                              </option>
                            ))}
                          </select>
                        </FormField>
                        <FormField meta={metaFor(fieldMeta, "designation")}>
                          <select
                            className="h-9 w-full rounded-md border border-[#dce3ec] px-3 text-[13px]"
                            {...form.register("designation")}
                          >
                            {designationOptions.map((opt) => (
                              <option key={opt.value || opt.label} value={opt.value}>
                                {opt.label}
                              </option>
                            ))}
                          </select>
                        </FormField>
                      </div>
                    </Section>

                    {isStudent ? (
                      <Section title="Student profile & schooling">
                        <div className="grid gap-4 sm:grid-cols-2">
                          <FormField meta={metaFor(studentMeta, "previous_school")}>
                            <Input className="h-9" {...form.register("previous_school")} />
                          </FormField>
                          <FormField meta={metaFor(studentMeta, "programme_code")}>
                            <Input className="h-9" {...form.register("programme_code")} />
                          </FormField>
                          <FormField meta={metaFor(studentMeta, "batch_label")}>
                            <Input className="h-9" {...form.register("batch_label")} />
                          </FormField>
                          <FormField meta={metaFor(studentMeta, "section_code")}>
                            <Input className="h-9" {...form.register("section_code")} />
                          </FormField>
                          <FormField meta={metaFor(studentMeta, "blood_group")}>
                            <select
                              className="h-9 w-full rounded-md border border-[#dce3ec] px-3 text-[13px]"
                              {...form.register("blood_group")}
                            >
                              {(data.blood_group_options ?? []).map((opt) => (
                                <option key={opt.value || opt.label} value={opt.value}>
                                  {opt.label}
                                </option>
                              ))}
                            </select>
                          </FormField>
                          <FormField meta={metaFor(studentMeta, "nationality")}>
                            <select
                              className="h-9 w-full rounded-md border border-[#dce3ec] px-3 text-[13px]"
                              {...form.register("nationality")}
                            >
                              {(data.nationality_options ?? []).map((opt) => (
                                <option key={opt.value || opt.label} value={opt.value}>
                                  {opt.label}
                                </option>
                              ))}
                            </select>
                          </FormField>
                          <FormField meta={metaFor(studentMeta, "guardian_name")}>
                            <Input className="h-9" {...form.register("guardian_name")} />
                          </FormField>
                          <FormField meta={metaFor(studentMeta, "guardian_relationship")}>
                            <select
                              className="h-9 w-full rounded-md border border-[#dce3ec] px-3 text-[13px]"
                              {...form.register("guardian_relationship")}
                            >
                              {(data.guardian_relationship_options ?? []).map((opt) => (
                                <option key={opt.value || opt.label} value={opt.value}>
                                  {opt.label}
                                </option>
                              ))}
                            </select>
                          </FormField>
                          <FormField meta={metaFor(studentMeta, "guardian_mobile")}>
                            <Input className="h-9" {...form.register("guardian_mobile")} />
                          </FormField>
                        </div>
                        <div className="mt-4 grid gap-4">
                          <FormField meta={metaFor(studentMeta, "permanent_address")}>
                            <textarea
                              className="min-h-[72px] w-full rounded-md border border-[#dce3ec] px-3 py-2 text-[13px]"
                              {...form.register("permanent_address")}
                            />
                          </FormField>
                          <FormField meta={metaFor(studentMeta, "current_address")}>
                            <textarea
                              className="min-h-[72px] w-full rounded-md border border-[#dce3ec] px-3 py-2 text-[13px]"
                              {...form.register("current_address")}
                            />
                          </FormField>
                        </div>
                      </Section>
                    ) : (
                      <Section title="Staff profile">
                        <div className="grid gap-4 sm:grid-cols-2">
                          <FormField meta={metaFor(staffMeta, "specialization")}>
                            <Input className="h-9" {...form.register("specialization")} />
                          </FormField>
                          <FormField meta={metaFor(staffMeta, "experience_years")}>
                            <Input className="h-9" inputMode="decimal" {...form.register("experience_years")} />
                          </FormField>
                        </div>
                      </Section>
                    )}

                    <Section title="Photo & documents">
                      <div className="space-y-4">
                        {(
                          [
                            ["profile_photo", "profile_photo_ref", "Profile photo"],
                            ["identity_document", "identity_document_ref", "ID / admission document"],
                            ["supporting_document", "supporting_document_ref", "Supporting document"],
                          ] as const
                        ).map(([kind, field, label]) => {
                          const refValue = form.watch(field);
                          return (
                            <div key={kind} className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                              <div>
                                <p className="text-[13px] font-medium text-[#374151]">{label}</p>
                                {refValue ? (
                                  <p className="text-[11px] text-[#10b981]">Uploaded</p>
                                ) : (
                                  <p className="text-[11px] text-[#9ca3af]">Optional · JPG, PNG or PDF</p>
                                )}
                              </div>
                              <Input
                                type="file"
                                accept="image/*,.pdf"
                                className="h-9 max-w-xs text-[12px]"
                                disabled={uploadingKind === kind}
                                onChange={(e) =>
                                  void handleProvisioningUpload(kind, field, e.target.files?.[0])
                                }
                              />
                            </div>
                          );
                        })}
                      </div>
                    </Section>
                  </>
                ) : null}

                {step === "role_access" ? (
                  <Section title={data.sections.find((s) => s.key === "role_access")?.title ?? "Role & access"}>
                    <div className="grid gap-4 sm:grid-cols-2">
                      <FormField meta={metaFor(fieldMeta, "campus_id")}>
                        <select
                          className="h-9 w-full rounded-md border border-[#dce3ec] px-3 text-[13px]"
                          {...form.register("campus_id")}
                        >
                          {data.campus_options.map((opt) => (
                            <option key={opt.value || opt.label} value={opt.value}>
                              {opt.label}
                            </option>
                          ))}
                        </select>
                      </FormField>
                      <FormField meta={metaFor(fieldMeta, "institution_role_id")}>
                        <select
                          className="h-9 w-full rounded-md border border-[#dce3ec] px-3 text-[13px]"
                          {...form.register("institution_role_id")}
                        >
                          {data.institution_role_options.map((opt) => (
                            <option key={opt.value || opt.label} value={opt.value}>
                              {opt.label}
                            </option>
                          ))}
                        </select>
                      </FormField>
                    </div>
                  </Section>
                ) : null}

                {step === "review" ? (
                  <Section title="Review & invite">
                    <dl className="divide-y divide-[#f1f5f9]">
                      {reviewLines.map((row) => (
                        <div key={row.label} className="flex justify-between gap-4 py-2.5 text-[13px]">
                          <dt className="text-[#6b7280]">{row.label}</dt>
                          <dd className="font-medium text-[#111827]">{row.value}</dd>
                        </div>
                      ))}
                    </dl>
                  </Section>
                ) : null}
              </div>

              <div className="space-y-5">
                {!sendInvite ? (
                  <Section title="Login credentials (admin-set)">
                    <p className="mb-3 text-[11px] text-[#6b7280]">
                      The user signs in with their official email and the password you set below.
                    </p>
                    <div className="space-y-3">
                      <FormField meta={{ key: "initial_password", label: "Password", required: true }}>
                        <Input
                          className="h-9"
                          type="password"
                          autoComplete="new-password"
                          {...form.register("initial_password")}
                        />
                      </FormField>
                      <FormField meta={{ key: "confirm_password", label: "Confirm password", required: true }}>
                        <Input
                          className="h-9"
                          type="password"
                          autoComplete="new-password"
                          value={confirmPassword}
                          onChange={(e) => setConfirmPassword(e.target.value)}
                        />
                      </FormField>
                    </div>
                  </Section>
                ) : null}

                <Section title="Account options">
                  <ul className="space-y-4">
                    {data.invitation_settings.map((toggle) => (
                      <li key={toggle.key} className="flex items-start justify-between gap-3">
                        <div>
                          <p className="text-[13px] font-medium text-[#111827]">{toggle.label}</p>
                          {toggle.description ? (
                            <p className="text-[11px] text-[#6b7280]">{toggle.description}</p>
                          ) : null}
                        </div>
                        <label className="relative inline-flex cursor-pointer items-center">
                          <input
                            type="checkbox"
                            className="peer sr-only"
                            checked={Boolean(form.watch(toggle.key as keyof CreateNewUserFormValues))}
                            onChange={(e) =>
                              form.setValue(toggle.key as keyof CreateNewUserFormValues, e.target.checked, {
                                shouldDirty: true,
                              })
                            }
                          />
                          <span className="h-5 w-9 rounded-full bg-[#e5e7eb] after:absolute after:left-0.5 after:top-0.5 after:size-4 after:rounded-full after:bg-white after:transition peer-checked:bg-[#245dd8] peer-checked:after:translate-x-4" />
                        </label>
                      </li>
                    ))}
                  </ul>
                </Section>

                <Section title="Before you continue">
                  <ul className="space-y-4">
                    {checks.map((check) => (
                      <li key={check.key} className="flex gap-2">
                        <CheckIcon
                          className={cn(
                            "mt-0.5 size-4 shrink-0",
                            check.tone === "success" ? "text-[#10b981]" : "text-[#d1d5db]",
                          )}
                          aria-hidden
                        />
                        <div className="min-w-0 flex-1">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <p className="text-[13px] font-medium text-[#111827]">{check.title}</p>
                            <ValidationBadge check={check} />
                          </div>
                          <p className="text-[11px] text-[#6b7280]">{check.subtitle}</p>
                        </div>
                      </li>
                    ))}
                  </ul>
                </Section>
              </div>
            </div>

            <footer className="flex flex-col gap-3 border-t border-[#e8ecf2] pt-4 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-[11px] text-[#9ca3af]">{data.audit_footer_note}</p>
              <div className="flex flex-wrap gap-2">
                <Link
                  href={data.cancel_href}
                  className="inline-flex h-9 items-center rounded-md border border-transparent px-4 text-xs font-medium text-[#6b7280] hover:text-[#374151]"
                >
                  {data.cancel_label}
                </Link>
                <button
                  type="button"
                  disabled={isBusy}
                  onClick={() => void handleSaveDraft()}
                  className="inline-flex h-9 items-center rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb] disabled:opacity-50"
                >
                  {data.save_draft_label}
                </button>
                {nextStep && step !== "review" ? (
                  <button
                    type="button"
                    disabled={isBusy}
                    onClick={() => void goNext()}
                    className="inline-flex h-9 items-center rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8] disabled:opacity-50"
                  >
                    {data.next_step_prefix}: {nextStep.label} →
                  </button>
                ) : (
                  <button
                    type="button"
                    disabled={isBusy}
                    onClick={() => void handleSubmitInvite()}
                    className="inline-flex h-9 items-center rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8] disabled:opacity-50"
                  >
                    {data.create_invite_label}
                  </button>
                )}
              </div>
            </footer>
          </>
        ) : null}
      </QueryState>
    </div>
  );
}