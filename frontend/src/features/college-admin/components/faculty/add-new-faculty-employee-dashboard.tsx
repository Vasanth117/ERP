"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { CheckIcon } from "@/components/icons/erp/generated/check";
import { ChevronLeftIcon } from "@/components/icons/erp/generated/chevron-left";
import { KeyIcon } from "@/components/icons/erp/generated/key";
import { SaveIcon } from "@/components/icons/erp/generated/save";
import { UserIcon } from "@/components/icons/erp/generated/user";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useAddNewFacultyEmployeePage,
  useCreateAddNewFacultyEmployee,
  useSaveAddNewFacultyEmployeeDraft,
} from "@/features/college-admin/hooks/use-add-new-faculty-employee";
import type { AddNewFacultyEmployeeFormValues } from "@/features/college-admin/types/add-new-faculty-employee";
import type { InstitutionFieldMeta } from "@/features/college-admin/types/institution";
import { cn } from "@/lib/utils";

function metaFor(fieldMeta: InstitutionFieldMeta[], key: string) {
  return fieldMeta.find((row) => row.key === key);
}

function FormField({ meta, children }: { meta?: InstitutionFieldMeta; children: React.ReactNode }) {
  if (!meta) return null;
  return (
    <div className={cn("space-y-1.5", meta.field_type === "textarea" ? "sm:col-span-2" : undefined)}>
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

function WizardStepper({
  steps,
  activeKey,
  onStep,
}: {
  steps: { key: string; label: string; step_number: number; status: string }[];
  activeKey: string;
  onStep: (key: string) => void;
}) {
  return (
    <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white px-4 py-4 shadow-[0_1px_2px_rgba(15,23,42,0.04)] sm:px-6">
      <div className="flex flex-wrap items-center gap-y-3 sm:flex-nowrap">
        {steps.map((wizardStep, index) => {
          const active = wizardStep.key === activeKey;
          const done = wizardStep.status === "done";
          return (
            <div key={wizardStep.key} className="flex min-w-0 flex-1 items-center last:flex-none">
              <button
                type="button"
                onClick={() => onStep(wizardStep.key)}
                className={cn(
                  "flex size-8 shrink-0 items-center justify-center rounded-full text-[13px] font-semibold tabular-nums transition-colors",
                  active && "border-2 border-[#245dd8] bg-white text-[#245dd8]",
                  !active && !done && "border border-[#e5e7eb] bg-[#f9fafb] text-[#9ca3af]",
                  done && "border-2 border-[#245dd8] bg-[#245dd8] text-white",
                )}
                aria-current={active ? "step" : undefined}
              >
                {done ? <CheckIcon className="size-3.5" strokeWidth={2.5} aria-hidden /> : wizardStep.step_number}
              </button>
              <button
                type="button"
                onClick={() => onStep(wizardStep.key)}
                className={cn(
                  "ml-2 hidden truncate text-left text-[12px] sm:inline sm:text-[13px]",
                  active ? "font-semibold text-[#111827]" : "font-medium text-[#9ca3af]",
                )}
              >
                {wizardStep.label}
              </button>
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


const STEP_TITLES: Record<string, string> = {
  personal: "Personal details",
  employment: "Employment details",
  qualifications: "Qualifications",
  documents: "Documents",
  account: "Account setup",
};

const selectClassName = "h-9 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px] text-[#111827]";

export function AddNewFacultyEmployeeDashboard() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const stepParam = useMemo(() => searchParams.get("step") ?? undefined, [searchParams]);

  const pageQuery = useAddNewFacultyEmployeePage();
  const saveDraft = useSaveAddNewFacultyEmployeeDraft();
  const createRecord = useCreateAddNewFacultyEmployee();

  const data = pageQuery.data;
  const form = useForm<AddNewFacultyEmployeeFormValues>({ values: data?.form });

  const [activeStep, setActiveStep] = useState("personal");

  useEffect(() => {
    if (data?.current_step_key) setActiveStep(data.current_step_key);
  }, [data?.current_step_key]);

  useEffect(() => {
    if (stepParam) setActiveStep(stepParam);
  }, [stepParam]);

  const fieldMeta = data?.field_meta ?? [];
  const toPayload = (values: AddNewFacultyEmployeeFormValues) => ({ ...values });

  const persistStep = (stepKey: string) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("step", stepKey);
    router.replace(`/college-admin/faculty/add-new-faculty-employee?${params.toString()}`);
    setActiveStep(stepKey);
  };

  const handleSaveDraft = form.handleSubmit((values) => {
    if (!data) return;
    saveDraft.mutate(
      { draft_id: data.draft_id, step_key: activeStep, values: toPayload(values) },
      {
        onSuccess: () => toast.success("Draft saved"),
        onError: (e: Error) => toast.error(e.message),
      },
    );
  });

  const handleCreate = form.handleSubmit((values) => {
    if (!data) return;
    saveDraft.mutate(
      { draft_id: data.draft_id, step_key: activeStep, values: toPayload(values) },
      {
        onSuccess: () => {
          createRecord.mutate(
            { draft_id: data.draft_id, values: toPayload(values) },
            {
              onSuccess: (res) => {
                toast.success("Employee record created");
                router.push(res.detail_href);
              },
              onError: (e: Error) => toast.error(e.message),
            },
          );
        },
        onError: (e: Error) => toast.error(e.message),
      },
    );
  });

  const isBusy = saveDraft.isPending || createRecord.isPending;

  return (
    <div className="space-y-5" data-figma-frame="159:3741">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <div className="flex items-center gap-1">
            <Link
              href={data?.back_href ?? "/college-admin/faculty/employee-directory"}
              className="inline-flex size-8 shrink-0 items-center justify-center rounded-md text-[#374151] hover:bg-[#f3f4f6]"
              aria-label={data?.back_label ?? "Back"}
            >
              <ChevronLeftIcon className="size-5" />
            </Link>
            <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
              {data?.page_title ?? "Add New Faculty / Employee"}
            </h2>
          </div>
          <p className="mt-1 pl-9 text-[14px] text-[#6b7280]">
            {data?.page_subtitle ?? "Create a staff record and login"}
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
            onClick={() => void handleCreate()}
            className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8] disabled:opacity-50"
          >
            <CheckIcon className="size-3.5" aria-hidden />
            {data?.create_label ?? "Create"}
          </button>
        </div>
      </div>

      {data ? (
        <WizardStepper steps={data.steps} activeKey={activeStep} onStep={persistStep} />
      ) : null}

      <QueryState
        isLoading={pageQuery.isLoading}
        isError={pageQuery.isError}
        error={pageQuery.error}
        onRetry={() => void pageQuery.refetch()}
      >
        {data ? (
          <>
            <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_300px]">
              <div className="space-y-5">
                <Section title={STEP_TITLES[activeStep] ?? "Details"}>
                  {activeStep === "personal" ? (
                    <div className="grid gap-4 sm:grid-cols-2">
                      <FormField meta={metaFor(fieldMeta, "full_name")}>
                        <Input className="h-9" {...form.register("full_name")} />
                      </FormField>
                      <FormField meta={metaFor(fieldMeta, "mobile")}>
                        <Input className="h-9" {...form.register("mobile")} />
                      </FormField>
                      <FormField meta={metaFor(fieldMeta, "date_of_birth")}>
                        <Input className="h-9" type="date" {...form.register("date_of_birth")} />
                      </FormField>
                      <FormField meta={metaFor(fieldMeta, "gender")}>
                        <select className={selectClassName} {...form.register("gender")}>
                          {data.gender_options.map((opt) => (
                            <option key={opt.value || opt.label} value={opt.value}>
                              {opt.label}
                            </option>
                          ))}
                        </select>
                      </FormField>
                      <FormField meta={metaFor(fieldMeta, "residential_address")}>
                        <textarea
                          className="min-h-[88px] w-full rounded-md border border-[#dce3ec] px-3 py-2 text-[13px]"
                          {...form.register("residential_address")}
                        />
                      </FormField>
                    </div>
                  ) : null}

                  {activeStep === "employment" ? (
                    <div className="grid gap-4 sm:grid-cols-2">
                      <FormField meta={metaFor(fieldMeta, "employee_type")}>
                        <select className={selectClassName} {...form.register("employee_type")}>
                          {data.employee_type_options.map((opt) => (
                            <option key={opt.value} value={opt.value}>
                              {opt.label}
                            </option>
                          ))}
                        </select>
                      </FormField>
                      <FormField meta={metaFor(fieldMeta, "department_id")}>
                        <select className={selectClassName} {...form.register("department_id")}>
                          {data.department_options.map((opt) => (
                            <option key={opt.value || opt.label} value={opt.value}>
                              {opt.label}
                            </option>
                          ))}
                        </select>
                      </FormField>
                      <FormField meta={metaFor(fieldMeta, "designation")}>
                        <select className={selectClassName} {...form.register("designation")}>
                          {data.designation_options.map((opt) => (
                            <option key={opt.value || opt.label} value={opt.value}>
                              {opt.label}
                            </option>
                          ))}
                        </select>
                      </FormField>
                      <FormField meta={metaFor(fieldMeta, "joining_date")}>
                        <Input className="h-9" type="date" {...form.register("joining_date")} />
                      </FormField>
                      <FormField meta={metaFor(fieldMeta, "reporting_to")}>
                        <select className={selectClassName} {...form.register("reporting_to")}>
                          {data.reporting_to_options.map((opt) => (
                            <option key={opt.value || opt.label} value={opt.value}>
                              {opt.label}
                            </option>
                          ))}
                        </select>
                      </FormField>
                      <FormField meta={metaFor(fieldMeta, "employment_status")}>
                        <select className={selectClassName} {...form.register("employment_status")}>
                          {data.employment_status_options.map((opt) => (
                            <option key={opt.value} value={opt.value}>
                              {opt.label}
                            </option>
                          ))}
                        </select>
                      </FormField>
                      <FormField meta={metaFor(fieldMeta, "contract_end_date")}>
                        <Input className="h-9" type="date" {...form.register("contract_end_date")} />
                      </FormField>
                      <FormField meta={metaFor(fieldMeta, "official_email")}>
                        <Input className="h-9" type="email" {...form.register("official_email")} />
                      </FormField>
                    </div>
                  ) : null}

                  {activeStep === "qualifications" ? (
                    <div className="grid gap-4 sm:grid-cols-2">
                      <FormField meta={metaFor(fieldMeta, "degree")}>
                        <Input className="h-9" {...form.register("degree")} />
                      </FormField>
                      <FormField meta={metaFor(fieldMeta, "institution")}>
                        <Input className="h-9" {...form.register("institution")} />
                      </FormField>
                      <FormField meta={metaFor(fieldMeta, "qualification_year")}>
                        <Input className="h-9" {...form.register("qualification_year")} />
                      </FormField>
                      <FormField meta={metaFor(fieldMeta, "specialization")}>
                        <Input className="h-9" {...form.register("specialization")} />
                      </FormField>
                      <FormField meta={metaFor(fieldMeta, "experience_years")}>
                        <Input className="h-9" {...form.register("experience_years")} />
                      </FormField>
                    </div>
                  ) : null}

                  {activeStep === "documents" ? (
                    <ul className="space-y-3">
                      {data.document_checklist.map((item) => (
                        <li key={item.value} className="flex items-center gap-2 text-[13px] text-[#374151]">
                          <input
                            type="checkbox"
                            className="size-4 rounded border-[#dce3ec]"
                            {...form.register(
                              item.value === "ids_verified"
                                ? "document_ids_verified"
                                : item.value === "degree_certificates"
                                  ? "document_degree_certificates"
                                  : "document_experience",
                            )}
                          />
                          {item.label}
                        </li>
                      ))}
                    </ul>
                  ) : null}

                  {activeStep === "account" ? (
                    <div className="grid max-w-md gap-4">
                      <FormField meta={metaFor(fieldMeta, "password")}>
                        <Input className="h-9" type="password" autoComplete="new-password" {...form.register("password")} />
                      </FormField>
                      <FormField meta={metaFor(fieldMeta, "confirm_password")}>
                        <Input
                          className="h-9"
                          type="password"
                          autoComplete="new-password"
                          {...form.register("confirm_password")}
                        />
                      </FormField>
                      <p className="text-[12px] text-[#6b7280]">
                        Login is created when you press Create. Official email becomes the username.
                      </p>
                    </div>
                  ) : null}
                </Section>
              </div>

              <div className="space-y-5">
                <Section title={data.access_card.title}>
                  <dl className="space-y-4 text-[13px]">
                    <div>
                      <dt className="text-[#6b7280]">Role</dt>
                      <dd className="mt-1 flex items-center gap-2 font-medium text-[#111827]">
                        <UserIcon className="size-4 text-[#245dd8]" aria-hidden />
                        {data.access_card.role_label}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-[#6b7280]">Login created</dt>
                      <dd className="mt-1 flex items-center gap-2 font-medium text-[#111827]">
                        <KeyIcon className="size-4 text-[#6b7280]" aria-hidden />
                        {data.access_card.login_created_label}
                      </dd>
                    </div>
                  </dl>
                </Section>
                <Section title={data.employee_id_card.title}>
                  <p className="text-[12px] text-[#6b7280]">{data.employee_id_card.next_id_label}</p>
                  <p className="mt-1 text-[20px] font-bold text-[#111827]">{data.employee_id_card.next_id_value}</p>
                  <p className="mt-3 text-[12px] text-[#9ca3af]">
                    {data.employee_id_card.format_label}: {data.employee_id_card.format_value}
                  </p>
                </Section>
              </div>
            </div>

          </>
        ) : null}
      </QueryState>
    </div>
  );
}
