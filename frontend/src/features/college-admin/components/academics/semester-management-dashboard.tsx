"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { useSearchParams } from "next/navigation";

import { CollegeAdminDownload } from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { PlusIcon } from "@/components/icons/erp/generated/plus";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { YearsSemestersSubNav } from "@/features/college-admin/components/academics/years-semesters-sub-nav";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useCreateSemesterManagementTerm,
  useSaveSemesterManagementSettings,
  useSemesterManagementPage,
} from "@/features/college-admin/hooks/use-semester-management";
import type { SemesterManagementTableRow } from "@/features/college-admin/types/semester-management";
import { cn } from "@/lib/utils";

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

type SettingsFormValues = {
  teaching_starts: string;
  last_instruction_day: string;
  mid_semester_exam_date: string;
  end_semester_exam_date: string;
  course_registration_opens: string;
  add_drop_deadline: string;
};

function toInputDate(value: string | null | undefined) {
  if (!value) return "";
  return value.length >= 10 ? value.slice(0, 10) : value;
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

export function SemesterManagementDashboard() {
  const searchParams = useSearchParams();
  const initialYearId = searchParams.get("year_id") ?? undefined;
  const initialTermId = searchParams.get("term_id") ?? undefined;

  const [yearId, setYearId] = useState(initialYearId);
  const [termId, setTermId] = useState(initialTermId);

  const { data, isLoading, isError, error, refetch } = useSemesterManagementPage({
    academic_year_id: yearId,
    term_id: termId,
  });
  const saveSettings = useSaveSemesterManagementSettings();
  const createTerm = useCreateSemesterManagementTerm();

  const form = useForm<SettingsFormValues>({
    defaultValues: {
      teaching_starts: "",
      last_instruction_day: "",
      mid_semester_exam_date: "",
      end_semester_exam_date: "",
      course_registration_opens: "",
      add_drop_deadline: "",
    },
  });

  const defaults = useMemo(() => data?.settings_form, [data?.settings_form]);

  useEffect(() => {
    if (!defaults) return;
    form.reset({
      teaching_starts: toInputDate(defaults.teaching_starts),
      last_instruction_day: toInputDate(defaults.last_instruction_day),
      mid_semester_exam_date: toInputDate(defaults.mid_semester_exam_date),
      end_semester_exam_date: toInputDate(defaults.end_semester_exam_date),
      course_registration_opens: toInputDate(defaults.course_registration_opens),
      add_drop_deadline: toInputDate(defaults.add_drop_deadline),
    });
  }, [defaults, form]);

  useEffect(() => {
    if (data?.selected_academic_year_id) setYearId(data.selected_academic_year_id);
    if (data?.selected_term_id) setTermId(data.selected_term_id);
  }, [data?.selected_academic_year_id, data?.selected_term_id]);

  const pickRow = (row: SemesterManagementTableRow) => {
    setTermId(row.term_id);
  };

  const handleExport = useCallback(() => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `semester-management-${new Date(data.generated_at).toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data]);

  const handleNewSemester = () => {
    if (!data?.selected_academic_year_id) return;
    const nextIndex = (data.semester_rows.length ?? 0) + 1;
    createTerm.mutate({
      academic_year_id: data.selected_academic_year_id,
      label: `Semester ${nextIndex}`,
    });
  };

  return (
    <div className="space-y-5" data-figma-frame="69:140138">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Semester Management"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">
            {data?.page_subtitle ?? "Configure semesters, teaching periods and academic milestones"}
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap items-center gap-2">
          <Link
            href={data?.years_button_href ?? "/college-admin/academics/academic-year-management"}
            className="inline-flex h-9 items-center rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb]"
          >
            {data?.years_button_label ?? "Years"}
          </Link>
          <button
            type="button"
            className="inline-flex h-9 items-center gap-1.5 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb] disabled:opacity-50"
            onClick={handleExport}
            disabled={isLoading || !data}
          >
            <CollegeAdminDownload className="size-3.5" aria-hidden />
            {data?.export_label ?? "Export"}
          </button>
          <button
            type="button"
            className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8] disabled:opacity-50"
            disabled={!data?.selected_academic_year_id || createTerm.isPending}
            onClick={handleNewSemester}
          >
            <PlusIcon className="size-3.5" aria-hidden />
            {data?.new_semester_label ?? "New semester"}
          </button>
        </div>
      </div>

      {data?.sub_nav?.length ? <YearsSemestersSubNav items={data.sub_nav} /> : null}

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            <div className="flex flex-wrap items-center gap-2">
              <select
                aria-label="Academic year"
                value={yearId ?? ""}
                onChange={(e) => {
                  setYearId(e.target.value || undefined);
                  setTermId(undefined);
                }}
                className="h-9 min-w-[12rem] rounded-md border border-[#dce3ec] bg-white px-3 text-[13px] text-[#374151]"
              >
                {data.year_filter_options.map((opt) => (
                  <option key={`${opt.value}-${opt.label}`} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_360px]">
              <div className="space-y-5">
                <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                  <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                    <h3 className="text-[14px] font-semibold text-[#111827]">{data.semesters_panel_title}</h3>
                  </div>
                  {data.semester_rows.length ? (
                    <div className="overflow-x-auto">
                      <table className="w-full min-w-[36rem] text-left text-[13px]">
                        <thead>
                          <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                            {data.table_headers.map((header, index) => (
                              <th key={header} className={cn("pb-3 font-medium", index === 0 ? "px-5" : "pr-3")}>
                                {header}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-[#f1f5f9]">
                          {data.semester_rows.map((row) => (
                            <tr
                              key={row.term_id}
                              className={cn(
                                "cursor-pointer hover:bg-[#f9fafb]",
                                data.selected_term_id === row.term_id && "bg-[#eff6ff]",
                              )}
                              onClick={() => pickRow(row)}
                            >
                              <td className="px-5 py-3 font-medium text-[#111827]">{row.label}</td>
                              <td className="py-3 pr-3 text-[#374151]">{row.period_label}</td>
                              <td className="py-3 pr-3 text-[#374151]">{row.week_label}</td>
                              <td className="py-3 pr-3 tabular-nums text-[#374151]">{row.course_count}</td>
                              <td className="py-3 pr-5">
                                <StatusPill label={row.status_label} tone={row.status_tone} />
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="px-5 py-8 text-sm text-[#9ca3af]">No semesters for this academic year yet.</p>
                  )}
                  <div className="flex items-center justify-between border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
                    <span>{data.semester_count_label}</span>
                    <Link href={data.manage_terms_href} className="font-medium text-[#245dd8] hover:underline">
                      {data.manage_terms_label}
                    </Link>
                  </div>
                </section>

                {data.settings_form && data.selected_term_id ? (
                  <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                    <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                      <h3 className="text-[14px] font-semibold text-[#111827]">{data.settings_panel_title}</h3>
                    </div>
                    <form
                      className="grid gap-4 px-5 py-4 sm:grid-cols-2"
                      onSubmit={form.handleSubmit((values) => {
                        saveSettings.mutate({
                          term_id: data.selected_term_id!,
                          settings: {
                            teaching_starts: values.teaching_starts || null,
                            last_instruction_day: values.last_instruction_day || null,
                            mid_semester_exam_date: values.mid_semester_exam_date || null,
                            end_semester_exam_date: values.end_semester_exam_date || null,
                            course_registration_opens: values.course_registration_opens || null,
                            add_drop_deadline: values.add_drop_deadline || null,
                          },
                        });
                      })}
                    >
                      {data.settings_field_meta.map((field) => (
                        <div key={field.key}>
                          <Label className="text-[13px] text-[#374151]">
                            {field.label}
                            {field.required ? <span className="text-[#dc2626]"> *</span> : null}
                          </Label>
                          <Input
                            type="date"
                            className="mt-1.5 h-9"
                            {...form.register(field.key as keyof SettingsFormValues)}
                          />
                        </div>
                      ))}
                      <div className="flex flex-col gap-3 border-t border-[#f1f5f9] pt-4 sm:col-span-2 sm:flex-row sm:items-center sm:justify-between">
                        <p className="text-[12px] text-[#6b7280]">{data.settings_form_note}</p>
                        <div className="flex gap-2">
                          <Button type="button" variant="outline" className="h-9 border-[#dce3ec] text-xs" onClick={() => form.reset()}>
                            {data.cancel_label}
                          </Button>
                          <Button type="submit" className="h-9 bg-[#245dd8] text-xs hover:bg-[#1f4fb8]" disabled={saveSettings.isPending}>
                            {data.save_label}
                          </Button>
                        </div>
                      </div>
                    </form>
                  </section>
                ) : null}
              </div>

              <div className="space-y-5">
                <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                  <h3 className="mb-4 text-[14px] font-semibold text-[#111827]">{data.progress_section_title}</h3>
                  {data.progress_items.length ? (
                    <ul className="space-y-4">
                      {data.progress_items.map((item) => (
                        <li key={item.key}>
                          <div className="mb-1.5 flex justify-between text-[13px]">
                            <span className="text-[#111827]">{item.label}</span>
                            <span className="tabular-nums text-[#6b7280]">{item.progress_percent}%</span>
                          </div>
                          <div className="h-1.5 overflow-hidden rounded-full bg-[#f1f5f9]">
                            <div
                              className="h-full rounded-full bg-[#245dd8]"
                              style={{ width: `${Math.min(100, item.progress_percent)}%` }}
                            />
                          </div>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm text-[#9ca3af]">Select a semester to view progress.</p>
                  )}
                </section>

                <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                  <h3 className="mb-3 text-[14px] font-semibold text-[#111827]">{data.linked_section_title}</h3>
                  <ul className="divide-y divide-[#f1f5f9]">
                    {data.linked_items.map((item) => (
                      <li key={item.key} className="flex items-start justify-between gap-3 py-3 first:pt-0">
                        <div>
                          <p className="text-[13px] font-medium text-[#111827]">{item.title}</p>
                          <p className="text-[12px] text-[#6b7280]">{item.subtitle}</p>
                        </div>
                        <StatusPill label={item.status_label} tone={item.status_tone} />
                      </li>
                    ))}
                  </ul>
                </section>
              </div>
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