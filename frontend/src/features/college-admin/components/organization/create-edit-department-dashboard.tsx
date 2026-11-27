"use client";

import Link from "next/link";
import { CollegeAdminModulePageHeading } from "@/features/college-admin/components/layout/college-admin-module-page-heading";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useMemo } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import {
  onCollegeAdminMutationError,
  useCollegeAdminValidation,
} from "@/features/college-admin/context/college-admin-validation-context";

import { CheckIcon } from "@/components/icons/erp/generated/check";
import { XIcon } from "@/components/icons/erp/generated/x";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { validateCreateEditDepartmentForm } from "@/features/college-admin/utils/create-edit-department-validation";
import {
  useCreateEditDepartmentPage,
  useSaveCreateEditDepartment,
} from "@/features/college-admin/hooks/use-create-edit-department";
import type {
  CreateEditDepartmentFormValues,
  CreateEditDepartmentTemplateOption,
} from "@/features/college-admin/types/create-edit-department";
import type { InstitutionFieldMeta } from "@/features/college-admin/types/institution";
import { cn } from "@/lib/utils";

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
      <div className="space-y-4 px-5 py-4">{children}</div>
    </section>
  );
}

function selectClassName() {
  return "h-9 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px] text-[#374151]";
}

function TemplateRow({
  item,
  onUse,
}: {
  item: CreateEditDepartmentTemplateOption;
  onUse: (departmentId: string) => void;
}) {
  return (
    <li className="flex items-start justify-between gap-3 border-b border-[#f1f5f9] py-3 last:border-0">
      <div>
        <p className="text-[13px] font-medium text-[#111827]">{item.title}</p>
        <p className="text-[12px] text-[#6b7280]">{item.subtitle}</p>
      </div>
      <button
        type="button"
        className="shrink-0 text-[12px] font-medium text-[#245dd8] hover:underline"
        onClick={() => onUse(item.department_id)}
      >
        {item.action_label}
      </button>
    </li>
  );
}

export function CreateEditDepartmentDashboard() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const departmentId = useMemo(
    () => searchParams.get("departmentId") ?? searchParams.get("department_id") ?? null,
    [searchParams],
  );

  const pageQuery = useCreateEditDepartmentPage(departmentId);
  const saveMutation = useSaveCreateEditDepartment(departmentId);
  const { showValidation } = useCollegeAdminValidation();

  const form = useForm<CreateEditDepartmentFormValues>({
    values: pageQuery.data?.form,
  });

  const data = pageQuery.data;
  const detailsMeta = data?.details_field_meta ?? [];
  const setupMeta = data?.setup_field_meta ?? [];

  const submit = useCallback(
    (mode: "create" | "draft") => {
      void form.handleSubmit((values) => {
        if (!data?.can_save) return;
        const clientMissing = validateCreateEditDepartmentForm(values, data, mode);
        if (clientMissing.length) {
          showValidation(
            "Missing required information",
            mode === "draft"
              ? "Department name and code are required to save a draft."
              : "Complete the required fields below before saving.",
            clientMissing,
          );
          return;
        }
        saveMutation.mutate(
          { mode, form: values },
          {
            onSuccess: (result) => {
              toast.success(mode === "draft" ? "Draft saved" : data.is_create ? "Department created" : "Changes saved");
              if (result.department_id && data.is_create) {
                router.push(`/college-admin/organization/department-details?departmentId=${result.department_id}`);
              } else if (!data.is_create) {
                void pageQuery.refetch();
              }
            },
            onError: onCollegeAdminMutationError,
          },
        );
      })();
    },
    [data, form, pageQuery, router, saveMutation, showValidation],
  );

  const applyTemplate = (templateDepartmentId: string) => {
    form.setValue("settings_template_department_id", templateDepartmentId);
    toast.message(templateDepartmentId ? "Template selected — settings apply on save" : "Using college defaults");
  };

  return (
    <div className="space-y-5" data-figma-frame="69:133115">
      <CollegeAdminModulePageHeading title={data?.page_title ?? "Create Department"} subtitle={data?.page_subtitle ?? "Add a new academic or administrative department"} actions={<><Link
            href={data?.cancel_href ?? "/college-admin/organization/all-departments"}
            className="inline-flex h-9 items-center gap-1.5 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb]"
          >
            <XIcon className="size-3.5" aria-hidden />
            {data?.cancel_label ?? "Cancel"}
          </Link>
          {data && !data.is_create ? (
            <button
              type="button"
              disabled={saveMutation.isPending}
              onClick={() => submit("create")}
              className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8] disabled:opacity-50"
            >
              <CheckIcon className="size-3.5" aria-hidden />
              {data.save_label}
            </button>
          ) : null}</>} />

      <QueryState
        isLoading={pageQuery.isLoading}
        isError={pageQuery.isError}
        error={pageQuery.error}
        onRetry={() => void pageQuery.refetch()}
      >
        {data ? (
          <form
            className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_320px]"
            onSubmit={(e) => e.preventDefault()}
          >
            <div className="space-y-5">
              <Section title={data.details_section_title}>
                <div className="grid gap-4 sm:grid-cols-2">
                  <FormField meta={metaFor(detailsMeta, "name")}>
                    <Input className="h-9" {...form.register("name")} />
                  </FormField>
                  <FormField meta={metaFor(detailsMeta, "department_code")}>
                    <Input
                      className="h-9 uppercase"
                      disabled={!data.is_create}
                      {...form.register("department_code")}
                    />
                  </FormField>
                </div>

                <FormField meta={metaFor(detailsMeta, "department_kind")}>
                  <div className="flex flex-wrap gap-4">
                    {data.department_kind_options.map((opt) => (
                      <label key={opt.value} className="inline-flex cursor-pointer items-center gap-2 text-[13px]">
                        <input
                          type="radio"
                          value={opt.value}
                          className="size-4 border-[#dce3ec] text-[#245dd8]"
                          {...form.register("department_kind")}
                        />
                        {opt.label}
                      </label>
                    ))}
                  </div>
                </FormField>

                <div className="grid gap-4 sm:grid-cols-2">
                  <FormField meta={metaFor(detailsMeta, "organization_unit_id")}>
                    <select className={selectClassName()} {...form.register("organization_unit_id")}>
                      {data.school_options.map((opt) => (
                        <option key={`${opt.value}-${opt.label}`} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </FormField>
                  <FormField meta={metaFor(detailsMeta, "campus_id")}>
                    <select className={selectClassName()} {...form.register("campus_id")}>
                      {data.campus_options.map((opt) => (
                        <option key={`${opt.value}-${opt.label}`} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </FormField>
                  <FormField meta={metaFor(detailsMeta, "establishment_year")}>
                    <Input
                      type="number"
                      className="h-9"
                      {...form.register("establishment_year", {
                        setValueAs: (v) => (v === "" || Number.isNaN(Number(v)) ? null : Number(v)),
                      })}
                    />
                  </FormField>
                  <FormField meta={metaFor(detailsMeta, "building_floor_label")}>
                    <select className={selectClassName()} {...form.register("building_floor_label")}>
                      {data.building_options.map((opt) => (
                        <option key={`${opt.value}-${opt.label}`} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </FormField>
                  <FormField meta={metaFor(detailsMeta, "contact_email")}>
                    <Input type="email" className="h-9" {...form.register("contact_email")} />
                  </FormField>
                </div>

                <FormField meta={metaFor(detailsMeta, "vision_mission")}>
                  <textarea
                    className="min-h-[6rem] w-full rounded-md border border-[#dce3ec] bg-white px-3 py-2 text-[13px] text-[#374151]"
                    {...form.register("vision_mission")}
                  />
                </FormField>
              </Section>

              <Section title={data.setup_section_title}>
                <FormField meta={metaFor(setupMeta, "head_user_id")}>
                  <select className={selectClassName()} {...form.register("head_user_id")}>
                    {data.head_options.map((opt) => (
                      <option key={`${opt.value}-${opt.label}`} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </FormField>
                <div className="grid gap-4 sm:grid-cols-2">
                  <FormField meta={metaFor(setupMeta, "approved_intake_ug")}>
                    <Input
                      type="number"
                      className="h-9"
                      {...form.register("approved_intake_ug", {
                        setValueAs: (v) => (v === "" || Number.isNaN(Number(v)) ? null : Number(v)),
                      })}
                    />
                  </FormField>
                  <FormField meta={metaFor(setupMeta, "aicte_approval_reference")}>
                    <Input className="h-9" placeholder="F.No. / date" {...form.register("aicte_approval_reference")} />
                  </FormField>
                  <FormField meta={metaFor(setupMeta, "cost_centre_code")}>
                    <Input
                      className="h-9"
                      list="department-cost-centres"
                      {...form.register("cost_centre_code")}
                    />
                    <datalist id="department-cost-centres">
                      {data.cost_centre_options
                        .filter((opt) => opt.value)
                        .map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                    </datalist>
                  </FormField>
                </div>
              </Section>
            </div>

            <div className="space-y-5">
              <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <h3 className="mb-3 text-[14px] font-semibold text-[#111827]">{data.copy_settings_title}</h3>
                <ul>
                  {data.template_options.map((item) => (
                    <TemplateRow key={item.template_key} item={item} onUse={applyTemplate} />
                  ))}
                </ul>
              </section>

              <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <h3 className="mb-3 text-[14px] font-semibold text-[#111827]">{data.checklist_title}</h3>
                <ul className="space-y-3 border-l border-[#e5e7eb] pl-4">
                  {data.checklist_steps.map((step) => (
                    <li key={step.key} className="relative pl-2">
                      <span
                        className={cn(
                          "absolute -left-[21px] top-1.5 size-2.5 rounded-full ring-4 ring-white",
                          step.state === "current"
                            ? "bg-[#245dd8]"
                            : step.state === "complete"
                              ? "bg-[#10b981]"
                              : "bg-[#d1d5db]",
                        )}
                      />
                      <p className="text-[13px] font-medium text-[#111827]">{step.label}</p>
                      <p className="text-[12px] text-[#6b7280]">{step.hint}</p>
                    </li>
                  ))}
                </ul>
              </section>
            </div>
          </form>
        ) : null}
      </QueryState>

      {data ? (
        <div className="sticky bottom-0 z-10 -mx-1 flex flex-col gap-3 border-t border-[#e8ecf2] bg-[#f8fafc]/95 px-1 py-4 backdrop-blur-sm sm:flex-row sm:items-center sm:justify-between">
          <p className="text-[12px] text-[#6b7280]">{data.footer_note}</p>
          <div className="flex flex-wrap gap-2">
            <Link
              href={data.cancel_href}
              className="inline-flex h-9 items-center rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-white"
            >
              {data.cancel_label}
            </Link>
            <button
              type="button"
              disabled={saveMutation.isPending}
              onClick={() => submit("draft")}
              className="inline-flex h-9 items-center rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb] disabled:opacity-50"
            >
              {data.save_draft_label}
            </button>
            <button
              type="button"
              disabled={saveMutation.isPending}
              onClick={() => submit("create")}
              className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8] disabled:opacity-50"
            >
              <CheckIcon className="size-3.5" aria-hidden />
              {data.save_label}
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}