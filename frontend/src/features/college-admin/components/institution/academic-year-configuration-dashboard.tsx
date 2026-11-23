"use client";
import { CollegeAdminPlusActionLabel } from "@/features/college-admin/components/ui/college-admin-plus-action";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";

import { CheckIcon } from "@/components/icons/erp/generated/check";
import { CopyIcon } from "@/components/icons/erp/generated/copy";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  getCollegeAdminErpIcon,
  resolveCollegeAdminIconSlug,
} from "@/features/college-admin/components/layout/college-admin-erp-icons";
import {
  InstitutionPageActionFooter,
  institutionActionButtonOutline,
  institutionActionButtonPrimary,
} from "@/features/college-admin/components/institution/institution-page-action-footer";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useAcademicYearConfigurationPage,
  useCopyAcademicYearFromPrevious,
  useCreateInstitutionAcademicYear,
  useSaveAcademicYearConfiguration,
} from "@/features/college-admin/hooks/use-institution";
import type {
  AcademicYearSemesterForm,
  AcademicYearTableRow,
  AcademicYearTimelineItem,
} from "@/features/college-admin/types/institution";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

const SEMESTER_FORM_ID = "academic-year-semester-form";

function StatusPill({ label, tone }: { label: string; tone: string }) {
  const styles: Record<string, string> = {
    success: "bg-[#ecfdf5] text-[#047857]",
    warning: "bg-[#fff7ed] text-[#c2410c]",
    info: "bg-[#eff6ff] text-[#1d4ed8]",
    muted: "bg-[#f3f4f6] text-[#6b7280]",
  };
  const dot: Record<string, string> = {
    success: "bg-[#10b981]",
    warning: "bg-[#f97316]",
    info: "bg-[#3b82f6]",
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

function toInputDate(value: string | null | undefined) {
  if (!value) return "";
  return value.length >= 10 ? value.slice(0, 10) : value;
}

function emptySemesterForm(): AcademicYearSemesterForm {
  return {
    odd_semester_start: null,
    odd_semester_end: null,
    even_semester_start: null,
    even_semester_end: null,
    summer_term_start: null,
    summer_term_end: null,
    year_end_closing: null,
  };
}

function TimelineItem({ item }: { item: AcademicYearTimelineItem }) {
  return (
    <li className="relative flex gap-3 pb-4 pl-5 last:pb-0">
      <span
        className={cn(
          "absolute left-0 top-1.5 size-2.5 rounded-full ring-4 ring-white",
          item.status_tone === "success"
            ? "bg-[#10b981]"
            : item.status_tone === "muted"
              ? "bg-[#9ca3af]"
              : "bg-[#3b82f6]",
        )}
      />
      <div className="min-w-0 flex-1">
        <p className="text-[13px] font-medium text-[#111827]">{item.title}</p>
        <p className="text-[12px] text-[#6b7280]">{item.date_label}</p>
      </div>
      {item.status_label ? (
        <StatusPill
          label={item.status_label}
          tone={item.status_tone === "success" ? "success" : "info"}
        />
      ) : null}
    </li>
  );
}


export function AcademicYearConfigurationDashboard() {
  const [selectedYearId, setSelectedYearId] = useState<string | undefined>();
  const { data, isLoading, isError, error, refetch } =
    useAcademicYearConfigurationPage(selectedYearId);
  const copyYear = useCopyAcademicYearFromPrevious();
  const createYear = useCreateInstitutionAcademicYear();
  const save = useSaveAcademicYearConfiguration();
  const activeYearId = selectedYearId ?? data?.selected_year_id ?? "";

  useEffect(() => {
    if (data?.selected_year_id && !selectedYearId) {
      setSelectedYearId(data.selected_year_id);
    }
  }, [data?.selected_year_id, selectedYearId]);

  const defaults = useMemo(() => {
    if (!data?.semester_form) return emptySemesterForm();
    const f = data.semester_form;
    return {
      odd_semester_start: f.odd_semester_start,
      odd_semester_end: f.odd_semester_end,
      even_semester_start: f.even_semester_start,
      even_semester_end: f.even_semester_end,
      summer_term_start: f.summer_term_start,
      summer_term_end: f.summer_term_end,
      year_end_closing: f.year_end_closing,
    };
  }, [data?.semester_form]);

  const form = useForm<AcademicYearSemesterForm>({ defaultValues: defaults });

  useEffect(() => {
    const normalized = {
      ...defaults,
      odd_semester_start: toInputDate(defaults.odd_semester_start),
      odd_semester_end: toInputDate(defaults.odd_semester_end),
      even_semester_start: toInputDate(defaults.even_semester_start),
      even_semester_end: toInputDate(defaults.even_semester_end),
      summer_term_start: toInputDate(defaults.summer_term_start),
      summer_term_end: toInputDate(defaults.summer_term_end),
      year_end_closing: toInputDate(defaults.year_end_closing),
    } as AcademicYearSemesterForm;
    form.reset(normalized);
  }, [defaults, form]);

  const pickYear = (row: AcademicYearTableRow) => {
    setSelectedYearId(row.year_id);
  };

  const submitSemesterForm = form.handleSubmit((values) => {
    if (!activeYearId) {
      toast.error("Select an academic year first");
      return;
    }
    const payload: AcademicYearSemesterForm = {
      ...values,
      odd_semester_start: values.odd_semester_start || null,
      odd_semester_end: values.odd_semester_end || null,
      even_semester_start: values.even_semester_start || null,
      even_semester_end: values.even_semester_end || null,
      summer_term_start: values.summer_term_start || null,
      summer_term_end: values.summer_term_end || null,
      year_end_closing: values.year_end_closing || null,
    };
    if (!payload.odd_semester_start || !payload.odd_semester_end) {
      toast.error("Enter odd semester start and end dates");
      return;
    }
    if (!payload.even_semester_start || !payload.even_semester_end) {
      toast.error("Enter even semester start and end dates");
      return;
    }
    save.mutate({ yearId: activeYearId, form: payload });
  });

  return (
    <div className="space-y-5" data-figma-frame="72:9235">
      <div className="min-w-0">
        <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
          {data?.page_title ?? "Academic Year Configuration"}
        </h2>
        <p className="mt-1 text-[14px] text-[#6b7280]">
          {data?.page_subtitle ?? "Define academic years, semesters and their key dates"}
        </p>
      </div>

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_360px]">
              <div className="space-y-5">
                <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                  <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                    <h3 className="text-[14px] font-semibold text-[#111827]">
                      {data.academic_years_table_title}
                    </h3>
                  </div>
                  {data.academic_years.length ? (
                    <div className="overflow-x-auto">
                      <table className="w-full min-w-[36rem] text-left text-[13px]">
                        <thead>
                          <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                            <th className="px-5 pb-3 font-medium">Academic year</th>
                            <th className="pb-3 pr-3 font-medium">Start</th>
                            <th className="pb-3 pr-3 font-medium">End</th>
                            <th className="pb-3 pr-3 font-medium">Semesters</th>
                            <th className="pb-3 pr-5 font-medium">Status</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-[#f1f5f9]">
                          {data.academic_years.map((row) => (
                            <tr
                              key={row.year_id}
                              className={cn(
                                "cursor-pointer hover:bg-[#f9fafb]",
                                activeYearId === row.year_id && "bg-[#eff6ff]",
                              )}
                              onClick={() => pickYear(row)}
                            >
                              <td className="px-5 py-3 font-medium text-[#111827]">{row.label}</td>
                              <td className="py-3 pr-3 text-[#374151]">{row.start_label}</td>
                              <td className="py-3 pr-3 text-[#374151]">{row.end_label}</td>
                              <td className="py-3 pr-3 text-[#374151]">{row.semesters_label}</td>
                              <td className="py-3 pr-5">
                                <StatusPill label={row.status_label} tone={row.status_tone} />
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="px-5 py-8 text-sm text-[#9ca3af]">No academic years yet.</p>
                  )}
                  <div className="flex items-center justify-between border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
                    <span>{data.academic_year_count_label}</span>
                    <Link href={data.archive_view_href} className="font-medium text-[#245dd8] hover:underline">
                      {data.archive_view_label}
                    </Link>
                  </div>
                </section>

                {data.semester_form && activeYearId ? (
                  <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                    <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                      <h3 className="text-[14px] font-semibold text-[#111827]">
                        {data.semester_section_title}
                      </h3>
                      <p className="mt-1 text-[12px] text-[#6b7280]">
                        Set semester dates for the selected year. Required fields are marked with *.
                      </p>
                    </div>
                    <form
                      id={SEMESTER_FORM_ID}
                      className="grid gap-4 px-5 py-4 sm:grid-cols-2"
                      onSubmit={submitSemesterForm}
                    >
                      {data.semester_field_meta.map((meta) => {
                        if (meta.key === "summer_term") {
                          return (
                            <div key={meta.key} className="sm:col-span-2">
                              <Label className="text-[13px] text-[#374151]">{meta.label}</Label>
                              <div className="mt-1.5 grid gap-2 sm:grid-cols-2">
                                <div>
                                  <span className="text-[11px] text-[#9ca3af]">Start</span>
                                  <Input type="date" className="mt-1 h-9" {...form.register("summer_term_start")} />
                                </div>
                                <div>
                                  <span className="text-[11px] text-[#9ca3af]">End</span>
                                  <Input type="date" className="mt-1 h-9" {...form.register("summer_term_end")} />
                                </div>
                              </div>
                            </div>
                          );
                        }
                        const fieldKey = meta.key as keyof AcademicYearSemesterForm;
                        return (
                          <div key={meta.key}>
                            <Label className="text-[13px] text-[#374151]">
                              {meta.label}
                              {meta.required ? <span className="text-[#dc2626]"> *</span> : null}
                            </Label>
                            <Input
                              type="date"
                              className="mt-1.5 h-9"
                              required={meta.required}
                              {...form.register(fieldKey)}
                            />
                          </div>
                        );
                      })}
                    </form>
                  </section>
                ) : !data.academic_years.length ? (
                  <section className="rounded-xl border border-dashed border-[#dce3ec] bg-[#f9fafb] px-5 py-8 text-center">
                    <p className="text-sm text-[#6b7280]">
                      Create a new academic year to configure semesters and dates.
                    </p>
                  </section>
                ) : null}
              </div>

              <div className="space-y-5">
                <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                  <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                    <h3 className="text-[14px] font-semibold text-[#111827]">
                      {data.year_timeline_title}
                    </h3>
                  </div>
                  {data.timeline.length ? (
                    <ul className="border-l border-[#e5e7eb] px-5 py-4">
                      {data.timeline.map((item) => (
                        <TimelineItem key={item.item_id} item={item} />
                      ))}
                    </ul>
                  ) : (
                    <p className="px-5 py-6 text-sm text-[#9ca3af]">No timeline milestones yet.</p>
                  )}
                </section>

                <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                  <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                    <h3 className="text-[14px] font-semibold text-[#111827]">
                      {data.linked_configuration_title}
                    </h3>
                  </div>
                  <ul className="divide-y divide-[#f1f5f9] px-5">
                    {data.linked_configuration.map((row) => {
                      const Icon = getCollegeAdminErpIcon(resolveCollegeAdminIconSlug(row.icon_slug));
                      return (
                        <li key={row.key} className="flex items-center justify-between gap-3 py-3.5">
                          <Link href={row.href} className="flex min-w-0 gap-3">
                            {Icon ? (
                              <Icon className="mt-0.5 size-[18px] shrink-0 text-[#9ca3af]" aria-hidden />
                            ) : null}
                            <span>
                              <span className="block text-[13px] font-medium text-[#111827]">
                                {row.title}
                              </span>
                              <span className="block text-[12px] text-[#6b7280]">{row.description}</span>
                            </span>
                          </Link>
                          <Link href={row.href} className="shrink-0 text-[12px] font-medium text-[#245dd8]">
                            Open →
                          </Link>
                        </li>
                      );
                    })}
                  </ul>
                </section>
              </div>
            </div>

            <InstitutionPageActionFooter>
              <Button
                type="button"
                variant="outline"
                className={institutionActionButtonOutline}
                disabled={copyYear.isPending || !data.academic_years.length}
                onClick={() =>
                  copyYear.mutate(undefined, {
                    onSuccess: (page) => {
                      if (page.selected_year_id) setSelectedYearId(page.selected_year_id);
                    },
                  })
                }
              >
                <CopyIcon className="size-3.5" aria-hidden />
                {data.copy_from_previous_label}
              </Button>
              <Button
                type="button"
                variant="outline"
                className={institutionActionButtonOutline}
                disabled={createYear.isPending}
                onClick={() =>
                  createYear.mutate(undefined, {
                    onSuccess: (page) => {
                      if (page.selected_year_id) setSelectedYearId(page.selected_year_id);
                    },
                  })
                }
              >
                <CollegeAdminPlusActionLabel iconClassName="size-3.5" label={data.new_academic_year_label } />
              </Button>
              <Button
                type="button"
                variant="outline"
                className={institutionActionButtonOutline}
                disabled={!activeYearId || !data.semester_form}
                onClick={() => {
                  if (data.semester_form) {
                    form.reset({
                      ...defaults,
                      odd_semester_start: toInputDate(defaults.odd_semester_start),
                      odd_semester_end: toInputDate(defaults.odd_semester_end),
                      even_semester_start: toInputDate(defaults.even_semester_start),
                      even_semester_end: toInputDate(defaults.even_semester_end),
                      summer_term_start: toInputDate(defaults.summer_term_start),
                      summer_term_end: toInputDate(defaults.summer_term_end),
                      year_end_closing: toInputDate(defaults.year_end_closing),
                    } as AcademicYearSemesterForm);
                  }
                }}
              >
                {data.cancel_label}
              </Button>
              <Button
                type="submit"
                form={SEMESTER_FORM_ID}
                className={institutionActionButtonPrimary}
                disabled={save.isPending || !activeYearId || !data.semester_form}
              >
                <CheckIcon className="size-3.5" aria-hidden />
                {data.save_label}
              </Button>
            </InstitutionPageActionFooter>
          </>
        ) : null}
      </QueryState>
    </div>
  );
}