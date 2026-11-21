"use client";

import type { ReactNode } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo } from "react";
import { useForm } from "react-hook-form";

import { CheckIcon } from "@/components/icons/erp/generated/check";
import { XIcon } from "@/components/icons/erp/generated/x";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { CourseCurriculumSubNav } from "@/features/college-admin/components/academics/course-curriculum-sub-nav";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useCourseConfigurationPage, useSaveCourseConfiguration } from "@/features/college-admin/hooks/use-course-curriculum";
import type { CourseConfigurationForm } from "@/features/college-admin/types/course-curriculum";
import { cn } from "@/lib/utils";

function ReqBadge({ label, tone }: { label: string; tone: string }) {
  const styles: Record<string, string> = {
    success: "bg-[#ecfdf5] text-[#047857]",
    info: "bg-[#eff6ff] text-[#1d4ed8]",
  };
  return (
    <span className={cn("rounded-full px-2 py-0.5 text-[10px] font-medium", styles[tone] ?? styles.info)}>
      {label}
    </span>
  );
}

export function CourseConfigurationDashboard() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const courseId = searchParams.get("course_id") ?? undefined;
  const mode = searchParams.get("mode") ?? undefined;

  const { data, isLoading, isError, error, refetch } = useCourseConfigurationPage({ course_id: courseId, mode });
  const save = useSaveCourseConfiguration();

  const form = useForm<CourseConfigurationForm>({
    defaultValues: data?.form,
  });

  const defaults = useMemo(() => data?.form, [data?.form]);

  useEffect(() => {
    if (defaults) form.reset(defaults);
  }, [defaults, form]);

  const optionsFor = (key: string) => {
    if (!data) return [];
    if (key === "department_id") return data.department_options;
    if (key === "course_type") return data.course_type_options;
    if (key === "semester_number") return data.semester_options;
    if (key === "regulation_label") return data.regulation_options;
    if (key === "exam_duration_label") return data.exam_duration_options;
    if (key === "exam_type_label") return data.exam_type_options;
    return [];
  };

  const onSubmit = (values: CourseConfigurationForm) => {
    save.mutate(
      { course_id: values.course_id, form: values },
      {
        onSuccess: (page) => {
          if (page.form.course_id) {
            router.replace(`/college-admin/academics/course-configuration?course_id=${encodeURIComponent(page.form.course_id)}`);
          }
        },
      },
    );
  };

  const renderField = (key: keyof CourseConfigurationForm, meta: { label: string; required: boolean; field_type: string }) => {
    const opts = optionsFor(key);
    if (meta.field_type === "select") {
      return (
        <select
          className="mt-1 flex h-9 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px]"
          {...form.register(key, {
            setValueAs: (v: string) =>
              key === "semester_number" ? (v === "" ? null : Number(v)) : v,
          })}
        >
          {opts.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      );
    }
    if (meta.field_type === "textarea") {
      return (
        <textarea
          className="mt-1 min-h-[88px] w-full rounded-md border border-[#dce3ec] px-3 py-2 text-[13px]"
          {...form.register(key)}
        />
      );
    }
    return (
      <Input
        className="mt-1 h-9"
        type={meta.field_type === "number" ? "number" : "text"}
        step={meta.field_type === "number" ? "any" : undefined}
        {...form.register(key, { valueAsNumber: meta.field_type === "number" })}
        readOnly={key === "credit_units" && meta.field_type === "number"}
      />
    );
  };

  const detailKeys = new Set([
    "course_code",
    "course_title",
    "department_id",
    "course_type",
    "semester_number",
    "regulation_label",
    "description",
  ]);
  const hourKeys = new Set(["lecture_hours", "tutorial_hours", "practical_hours", "credit_units"]);
  const assessKeys = new Set([
    "internal_assessment_label",
    "end_semester_exam_label",
    "exam_duration_label",
    "exam_type_label",
  ]);

  return (
    <div className="space-y-5" data-figma-frame="69:140676">
      {data?.sub_nav.length ? <CourseCurriculumSubNav items={data.sub_nav} /> : null}

      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="flex flex-wrap items-center gap-2">
          <h2 className="text-[22px] font-bold text-[#111827]">{data?.page_title ?? "Course Configuration"}</h2>
          {data ? (
            <span
              className={cn(
                "rounded-full px-2.5 py-0.5 text-[11px] font-medium",
                data.status_tone === "success" ? "bg-[#ecfdf5] text-[#047857]" : "bg-[#fff7ed] text-[#c2410c]",
              )}
            >
              {data.status_label}
            </span>
          ) : null}
          <p className="w-full text-[14px] text-[#6b7280]">{data?.page_subtitle}</p>
        </div>
        <div className="flex gap-2">
          <Link
            href="/college-admin/academics/subject-management"
            className="inline-flex h-9 items-center gap-1.5 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151]"
          >
            <XIcon className="size-3.5" />
            {data?.cancel_label ?? "Cancel"}
          </Link>
          <button
            type="button"
            disabled={save.isPending}
            onClick={form.handleSubmit(onSubmit)}
            className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8] disabled:opacity-50"
          >
            <CheckIcon className="size-3.5" />
            {data?.save_label ?? "Save course"}
          </button>
        </div>
      </div>

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <form className="grid gap-5 xl:grid-cols-3" onSubmit={form.handleSubmit(onSubmit)}>
            <div className="space-y-5 xl:col-span-2">
              <Section title={data.details_section_title}>
                <div className="grid gap-4 sm:grid-cols-2">
                  {data.field_meta
                    .filter((m) => detailKeys.has(m.key))
                    .map((meta) => (
                      <div key={meta.key} className={meta.key === "description" ? "sm:col-span-2" : undefined}>
                        <Label className="text-[12px] text-[#374151]">
                          {meta.label}
                          {meta.required ? " *" : ""}
                        </Label>
                        {renderField(meta.key as keyof CourseConfigurationForm, meta)}
                      </div>
                    ))}
                </div>
              </Section>
              <Section title={data.hours_section_title}>
                <div className="grid gap-4 sm:grid-cols-2">
                  {data.field_meta
                    .filter((m) => hourKeys.has(m.key))
                    .map((meta) => (
                      <div key={meta.key}>
                        <Label className="text-[12px] text-[#374151]">
                          {meta.label}
                          {meta.required ? " *" : ""}
                        </Label>
                        {renderField(meta.key as keyof CourseConfigurationForm, meta)}
                      </div>
                    ))}
                </div>
              </Section>
              <Section title={data.assessment_section_title}>
                <div className="grid gap-4 sm:grid-cols-2">
                  {data.field_meta
                    .filter((m) => assessKeys.has(m.key))
                    .map((meta) => (
                      <div key={meta.key}>
                        <Label className="text-[12px] text-[#374151]">
                          {meta.label}
                          {meta.required ? " *" : ""}
                        </Label>
                        {renderField(meta.key as keyof CourseConfigurationForm, meta)}
                      </div>
                    ))}
                </div>
              </Section>
              <p className="text-[12px] text-[#6b7280]">{data.form_note}</p>
              <div className="flex justify-end gap-2">
                <Link href="/college-admin/academics/subject-management" className="h-9 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium leading-9 text-[#374151]">
                  {data.cancel_label}
                </Link>
                <button type="submit" disabled={save.isPending} className="h-9 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white disabled:opacity-50">
                  {data.save_label}
                </button>
              </div>
            </div>
            <div className="space-y-4">
              <Section title={data.prerequisites_section_title}>
                {data.prerequisites.length ? (
                  <ul className="space-y-3">
                    {data.prerequisites.map((p) => (
                      <li key={p.prerequisite_id} className="text-[13px]">
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <p className="font-medium text-[#111827]">{p.title}</p>
                            {p.semester_hint ? <p className="text-[11px] text-[#9ca3af]">{p.semester_hint}</p> : null}
                          </div>
                          <ReqBadge label={p.requirement_label} tone={p.requirement_tone} />
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-[#9ca3af]">No prerequisites linked.</p>
                )}
              </Section>
              <Section title={data.offered_section_title}>
                {data.offered_to.length ? (
                  <ul className="space-y-2 text-[13px] text-[#374151]">
                    {data.offered_to.map((o, i) => (
                      <li key={`${o.programme_label}-${i}`}>
                        <p className="font-medium text-[#111827]">{o.programme_label}</p>
                        <p className="text-[11px] text-[#9ca3af]">{o.detail_label}</p>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-[#9ca3af]">Not mapped to programmes yet.</p>
                )}
              </Section>
              <Section title={data.outcomes_section_title} action={{ label: data.outcomes_edit_label, href: data.outcomes_edit_href }}>
                {data.outcomes_text ? (
                  <p className="whitespace-pre-wrap text-[12px] leading-relaxed text-[#374151]">{data.outcomes_text}</p>
                ) : (
                  <p className="text-sm text-[#9ca3af]">No learning outcomes recorded.</p>
                )}
              </Section>
            </div>
          </form>
        ) : null}
      </QueryState>
    </div>
  );
}

function Section({
  title,
  children,
  action,
}: {
  title: string;
  children: ReactNode;
  action?: { label: string; href: string };
}) {
  return (
    <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-[14px] font-semibold text-[#111827]">{title}</h3>
        {action ? (
          <Link href={action.href} className="text-[12px] font-medium text-[#245dd8] hover:underline">
            {action.label}
          </Link>
        ) : null}
      </div>
      {children}
    </section>
  );
}