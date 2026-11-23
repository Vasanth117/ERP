"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { ChevronLeftIcon } from "@/components/icons/erp/generated/chevron-left";
import { ChevronRightIcon } from "@/components/icons/erp/generated/chevron-right";
import { SaveIcon } from "@/components/icons/erp/generated/save";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { YearsSemestersSubNav } from "@/features/college-admin/components/academics/years-semesters-sub-nav";
import {
  CollegeAdminPanelChromeHeader,
  CollegeAdminPanelShell,
} from "@/features/college-admin/components/ui/dashboard-panel-ui";
import { CollegeAdminWizardStepper } from "@/features/college-admin/components/ui/college-admin-wizard-stepper";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useNewAcademicYearWizardPage,
  useSaveAcademicYearWizardDraft,
} from "@/features/college-admin/hooks/use-new-academic-year-wizard";
import type { AcademicYearWizardFormValues } from "@/features/college-admin/types/new-academic-year-wizard";
import type { InstitutionFieldMeta } from "@/features/college-admin/types/institution";
import { cn } from "@/lib/utils";

function metaFor(fieldMeta: InstitutionFieldMeta[], key: string) {
  return fieldMeta.find((row) => row.key === key);
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <CollegeAdminPanelShell>
      <CollegeAdminPanelChromeHeader title={title} />
      <div className="px-5 py-4">{children}</div>
    </CollegeAdminPanelShell>
  );
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

export function CreateAcademicYearDashboard() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const draftIdParam = useMemo(() => searchParams.get("draft_id") ?? undefined, [searchParams]);

  const pageQuery = useNewAcademicYearWizardPage(draftIdParam);
  const saveDraft = useSaveAcademicYearWizardDraft();
  const data = pageQuery.data;

  const form = useForm<AcademicYearWizardFormValues>({ values: data?.form });
  const [activeStep, setActiveStep] = useState("year_identity");

  useEffect(() => {
    if (data?.current_step_key) setActiveStep(data.current_step_key);
  }, [data?.current_step_key]);

  useEffect(() => {
    if (data?.draft_id && !draftIdParam) {
      const params = new URLSearchParams(searchParams.toString());
      params.set("draft_id", data.draft_id);
      router.replace(`/college-admin/academics/create-academic-year?${params.toString()}`);
    }
  }, [data?.draft_id, draftIdParam, router, searchParams]);

  const fieldMeta = data?.field_meta ?? [];
  const isBusy = saveDraft.isPending;

  const persist = (opts: { advance?: boolean; finalize?: boolean }) =>
    form.handleSubmit((values) => {
      if (!data) return;
      if (
        values.start_date &&
        values.end_date &&
        values.end_date < values.start_date
      ) {
        toast.error("End date must be on or after the start date.");
        return;
      }
      saveDraft.mutate(
        {
          draft_id: data.draft_id,
          step_key: activeStep,
          advance: opts.advance,
          finalize: opts.finalize,
          values: { ...values, copy_from_year_id: values.copy_from_year_id || null },
        },
        {
          onSuccess: (res) => {
            if (res.details_href) {
              toast.success("Academic year created");
              router.replace(res.details_href);
              return;
            }
            if (res.page) {
              setActiveStep(res.page.current_step_key);
              if (opts.advance) toast.success("Saved — continue to the next step");
              else toast.success("Draft saved");
            }
          },
        },
      );
    });

  const subNav = [
    { key: "years", label: "Years", href: "/college-admin/academics/academic-year-management", active: false },
    { key: "semesters", label: "Semesters", href: "/college-admin/academics/semester-management", active: false },
    {
      key: "calendar",
      label: "Academic calendar",
      href: "/college-admin/academics/academic-calendar-configuration",
      active: false,
    },
  ];

  return (
    <div className="space-y-5">
      <YearsSemestersSubNav items={subNav} />

      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <div className="flex items-center gap-1">
            <Link
              href={data?.back_href ?? "/college-admin/academics/academic-year-management"}
              className="inline-flex size-8 shrink-0 items-center justify-center rounded-md text-[#374151] hover:bg-[#f3f4f6]"
              aria-label={data?.back_label ?? "Back"}
            >
              <ChevronLeftIcon className="size-5" />
            </Link>
            <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
              {data?.page_title ?? "New academic year"}
            </h2>
          </div>
          <p className="mt-1 pl-9 text-[14px] text-[#6b7280]">
            {data?.step_position_label ?? data?.page_subtitle ?? "Set up a new academic year"}
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <button
            type="button"
            disabled={!data || isBusy}
            onClick={() => void persist({})()}
            className="inline-flex h-9 items-center gap-1.5 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb] disabled:opacity-50"
          >
            <SaveIcon className="size-3.5" aria-hidden />
            {data?.save_draft_label ?? "Save draft"}
          </button>
          {activeStep === "review" ? (
            <button
              type="button"
              disabled={!data || isBusy}
              onClick={() => void persist({ finalize: true })()}
              className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8] disabled:opacity-50"
            >
              {data?.finalize_label ?? "Create academic year"}
            </button>
          ) : (
            <button
              type="button"
              disabled={!data || isBusy}
              onClick={() => void persist({ advance: true })()}
              className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8] disabled:opacity-50"
            >
              {data?.continue_label ?? "Continue"}
              <ChevronRightIcon className="size-3.5" aria-hidden />
            </button>
          )}
        </div>
      </div>

      {data ? <CollegeAdminWizardStepper steps={data.steps} activeKey={activeStep} /> : null}

      <QueryState isLoading={pageQuery.isLoading} isError={pageQuery.isError} error={pageQuery.error} onRetry={() => void pageQuery.refetch()}>
        {data ? (
          <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_320px]">
            <div className="space-y-5">
              {activeStep === "year_identity" ? (
                <Section title="Year identity">
                  <div className="grid gap-4 sm:grid-cols-2">
                    <FormField meta={metaFor(fieldMeta, "label")}>
                      <Input className="h-9" placeholder="e.g. 2026–27" {...form.register("label", { required: true })} />
                    </FormField>
                    <FormField meta={metaFor(fieldMeta, "copy_from_year_id")}>
                      <select
                        className="h-9 w-full rounded-md border border-[#dce3ec] px-3 text-[13px]"
                        {...form.register("copy_from_year_id")}
                      >
                        {data.copy_from_options.map((opt) => (
                          <option key={`${opt.value}-${opt.label}`} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                    </FormField>
                  </div>
                </Section>
              ) : null}

              {activeStep === "calendar" ? (
                <Section title="Important dates">
                  <div className="grid gap-4 sm:grid-cols-2">
                    {(
                      [
                        "start_date",
                        "end_date",
                        "admission_intake_opens",
                        "summer_term_start",
                        "summer_term_end",
                        "year_end_closing",
                      ] as const
                    ).map((key) => (
                      <FormField key={key} meta={metaFor(fieldMeta, key)}>
                        <Input className="h-9" type="date" {...form.register(key)} />
                      </FormField>
                    ))}
                  </div>
                </Section>
              ) : null}

              {activeStep === "semesters" ? (
                <Section title="Semester structure">
                  <FormField meta={metaFor(fieldMeta, "semester_count")}>
                    <select className="h-9 w-full rounded-md border border-[#dce3ec] px-3 text-[13px]" {...form.register("semester_count")}>
                      {data.semester_count_options.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </FormField>
                </Section>
              ) : null}

              {activeStep === "review" ? (
                <Section title={data.summary_title}>
                  <dl className="divide-y divide-[#f1f5f9]">
                    {data.summary_items.map((item) => (
                      <div key={item.key} className="flex justify-between gap-4 py-3 text-[13px] first:pt-0 last:pb-0">
                        <dt className="text-[#6b7280]">{item.label}</dt>
                        <dd className="font-medium text-[#111827]">{item.value}</dd>
                      </div>
                    ))}
                  </dl>
                </Section>
              ) : null}
            </div>

            <aside className="space-y-3">
              <section className="rounded-xl border border-[#e8ecf2] bg-[#f8fafc] px-5 py-4 text-[12px] leading-relaxed text-[#6b7280]">
                {data.footer_disclaimer}
              </section>
            </aside>
          </div>
        ) : null}
      </QueryState>
    </div>
  );
}