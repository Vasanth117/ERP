"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useMemo } from "react";
import { useForm } from "react-hook-form";
import { onCollegeAdminMutationError } from "@/features/college-admin/context/college-admin-validation-context";
import { toast } from "sonner";

import { CheckIcon } from "@/components/icons/erp/generated/check";
import { UserIcon } from "@/components/icons/erp/generated/user";
import { XIcon } from "@/components/icons/erp/generated/x";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useDepartmentDesignationAssignmentPage,
  useSaveDepartmentDesignationAssignment,
} from "@/features/college-admin/hooks/use-department-designation-assignment";
import type { DepartmentDesignationAssignmentFormValues } from "@/features/college-admin/types/department-designation-assignment";
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

function StatusPill({ label, tone }: { label: string; tone: string }) {
  const styles: Record<string, string> = {
    success: "bg-[#ecfdf5] text-[#047857]",
    warning: "bg-[#fff7ed] text-[#c2410c]",
    muted: "bg-[#f3f4f6] text-[#6b7280]",
  };
  const dot: Record<string, string> = {
    success: "bg-[#10b981]",
    warning: "bg-[#f97316]",
    muted: "bg-[#9ca3af]",
  };
  const key = tone in styles ? tone : "muted";
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-medium", styles[key])}>
      <span className={cn("size-1.5 rounded-full", dot[key])} />
      {label}
    </span>
  );
}

const selectClassName = "h-9 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px] text-[#111827]";


export function DepartmentDesignationAssignmentDashboard() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const recordId = useMemo(
    () => searchParams.get("record_id") ?? searchParams.get("id") ?? undefined,
    [searchParams],
  );

  const pageQuery = useDepartmentDesignationAssignmentPage(recordId);
  const saveRecordId = pageQuery.data?.form.record_id ?? recordId ?? "";
  const saveMutation = useSaveDepartmentDesignationAssignment(saveRecordId);

  const form = useForm<DepartmentDesignationAssignmentFormValues>({
    values: pageQuery.data?.form,
  });

  const data = pageQuery.data;
  const isDirty = form.formState.isDirty;

  const approvalSteps = useMemo(() => {
    if (!data?.approval_steps) return [];
    if (!isDirty) return data.approval_steps;
    return data.approval_steps.map((step) =>
      step.key === "college_admin"
        ? { ...step, status_label: "Pending", tone: "warning" }
        : step,
    );
  }, [data?.approval_steps, isDirty]);

  const submitSave = form.handleSubmit((values) => {
    if (!saveRecordId) return;
    saveMutation.mutate(values as unknown as Record<string, unknown>, {
      onSuccess: () => {
        toast.success("Assignment saved");
        form.reset(values);
      },
      onError: onCollegeAdminMutationError,
    });
  });

  const isBusy = saveMutation.isPending;

  return (
    <div className="space-y-5" data-figma-frame="159:4430">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Department & Designation Assignment"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">
            {data?.page_subtitle ?? "Assign department, designation and reporting line"}
          </p>
        </div>
        {!data?.requires_record ? (
          <div className="flex shrink-0 flex-wrap gap-2">
            <Link
              href={data?.cancel_href ?? "/college-admin/faculty/faculty-directory"}
              className="inline-flex h-9 items-center gap-1.5 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb]"
            >
              <XIcon className="size-3.5" aria-hidden />
              {data?.cancel_label ?? "Cancel"}
            </Link>
            <button
              type="button"
              disabled={!data || isBusy}
              onClick={() => void submitSave()}
              className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8] disabled:opacity-50"
            >
              <CheckIcon className="size-3.5" aria-hidden />
              {data?.save_label ?? "Save assignment"}
            </button>
          </div>
        ) : null}
      </div>

      <QueryState
        isLoading={pageQuery.isLoading}
        isError={pageQuery.isError}
        error={pageQuery.error}
        onRetry={() => void pageQuery.refetch()}
      >
        {data?.requires_record ? (
          <Section title={data.select_employee_title ?? "Select employee"}>
            <p className="mb-4 text-sm text-[#6b7280]">{data.select_employee_hint}</p>
            {data.picker_rows.length ? (
              <ul className="divide-y divide-[#f1f5f9] rounded-lg border border-[#e8ecf2]">
                {data.picker_rows.map((row) => (
                  <li key={row.record_id}>
                    <Link
                      href={`/college-admin/faculty/department-designation-assignment?id=${encodeURIComponent(row.record_id)}`}
                      className="flex items-center justify-between gap-4 px-4 py-3 text-[13px] hover:bg-[#f9fafb]"
                    >
                      <span className="font-medium text-[#111827]">{row.label}</span>
                    </Link>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-[#9ca3af]">No faculty records yet.</p>
            )}
            {data.faculty_directory_href ? (
              <Link
                href={data.faculty_directory_href}
                className="mt-4 inline-flex text-sm font-medium text-[#245dd8] hover:underline"
              >
                {data.faculty_directory_label} →
              </Link>
            ) : null}
          </Section>
        ) : data ? (
          <>
            <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_300px]">
              <Section title={data.assignment_section_title}>
                <form
                  className="grid gap-4 sm:grid-cols-2"
                  onSubmit={(e) => {
                    e.preventDefault();
                    void submitSave();
                  }}
                >
                  <FormField meta={metaFor(data.field_meta, "record_id")}>
                    <select
                      className={selectClassName}
                      value={form.watch("record_id")}
                      onChange={(e) => {
                        const next = e.target.value;
                        form.setValue("record_id", next);
                        if (next) {
                          router.push(
                            `/college-admin/faculty/department-designation-assignment?id=${encodeURIComponent(next)}`,
                          );
                        }
                      }}
                    >
                      {data.employee_options.map((opt) => (
                        <option key={opt.value || opt.label} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                    {data.employee_display ? (
                      <p className="text-[11px] text-[#9ca3af]">{data.employee_display}</p>
                    ) : null}
                  </FormField>
                  <div className="hidden sm:block" aria-hidden />
                  <FormField meta={metaFor(data.field_meta, "department_id")}>
                    <select className={selectClassName} {...form.register("department_id")}>
                      {data.department_options.map((opt) => (
                        <option key={opt.value || opt.label} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </FormField>
                  <FormField meta={metaFor(data.field_meta, "designation")}>
                    <select className={selectClassName} {...form.register("designation")}>
                      {data.designation_options.map((opt) => (
                        <option key={opt.value || opt.label} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </FormField>
                  <FormField meta={metaFor(data.field_meta, "reporting_to")}>
                    <select className={selectClassName} {...form.register("reporting_to")}>
                      {data.reporting_to_options.map((opt) => (
                        <option key={opt.value || opt.label} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </FormField>
                  <FormField meta={metaFor(data.field_meta, "effective_from")}>
                    <Input className="h-9" type="date" {...form.register("effective_from")} />
                  </FormField>
                  <FormField meta={metaFor(data.field_meta, "reason")}>
                    <textarea
                      className="min-h-[5rem] w-full rounded-md border border-[#dce3ec] px-3 py-2 text-[13px]"
                      {...form.register("reason")}
                    />
                  </FormField>
                </form>
              </Section>

              <div className="space-y-5">
                <Section title={data.history_section_title}>
                  <ol className="space-y-4">
                    {data.history_items.map((item, index) => (
                      <li key={item.key} className="relative flex gap-3 pb-1">
                        {index < data.history_items.length - 1 ? (
                          <span className="absolute left-[5px] top-3 h-[calc(100%+4px)] w-px bg-[#e5e7eb]" aria-hidden />
                        ) : null}
                        <span
                          className={cn(
                            "relative z-[1] mt-1 size-2.5 shrink-0 rounded-full ring-4 ring-white",
                            item.tone === "success"
                              ? "bg-[#10b981]"
                              : item.tone === "info"
                                ? "bg-[#3b82f6]"
                                : "bg-[#d1d5db]",
                          )}
                        />
                        <div>
                          <p className="text-[13px] font-medium text-[#111827]">{item.title}</p>
                          <p className="text-[12px] text-[#6b7280]">{item.date_label}</p>
                        </div>
                      </li>
                    ))}
                  </ol>
                </Section>

                <Section title={data.approval_section_title}>
                  <ul className="space-y-4">
                    {approvalSteps.map((step) => (
                      <li key={step.key} className="flex items-start justify-between gap-3">
                        <div className="flex gap-3">
                          <UserIcon className="mt-0.5 size-4 shrink-0 text-[#9ca3af]" aria-hidden />
                          <div>
                            <p className="text-[13px] font-medium text-[#111827]">{step.label}</p>
                            <p className="text-[12px] text-[#6b7280]">{step.status_label}</p>
                          </div>
                        </div>
                        <StatusPill
                          label={step.tone === "success" ? "Done" : step.status_label}
                          tone={step.tone}
                        />
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