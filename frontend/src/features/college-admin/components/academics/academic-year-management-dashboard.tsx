"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";

import { CalendarDaysIcon } from "@/components/icons/erp/generated/calendar-days";
import { LockIcon } from "@/components/icons/erp/generated/lock";
import { PlusIcon } from "@/components/icons/erp/generated/plus";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { YearsSemestersSubNav } from "@/features/college-admin/components/academics/years-semesters-sub-nav";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useAcademicYearManagementPage,
  useCloseCurrentAcademicYear,
  useCreateAcademicYearManagement,
  useSaveAcademicYearManagementRules,
} from "@/features/college-admin/hooks/use-academic-year-management";
import type {
  AcademicYearCreateFormField,
  AcademicYearCreateFormOption,
  AcademicYearRuleToggle,
} from "@/features/college-admin/types/academic-year-management";
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

function RuleToggle({
  rule,
  checked,
  onChange,
}: {
  rule: AcademicYearRuleToggle;
  checked: boolean;
  onChange: (next: boolean) => void;
}) {
  return (
    <div className="flex items-start justify-between gap-3 py-3.5 first:pt-1">
      <div>
        <p className="text-[13px] font-medium text-[#111827]">{rule.title}</p>
        <p className="text-[12px] text-[#6b7280]">{rule.description}</p>
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        aria-label={rule.title}
        onClick={() => onChange(!checked)}
        className={cn(
          "relative h-6 w-11 shrink-0 rounded-full transition-colors",
          checked ? "bg-[#245dd8]" : "bg-[#d1d5db]",
        )}
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

function SelectField({
  label,
  value,
  onChange,
  options,
  required,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: AcademicYearCreateFormOption[];
  required?: boolean;
}) {
  return (
    <div>
      <Label className="text-[13px] text-[#374151]">
        {label}
        {required ? <span className="text-[#dc2626]"> *</span> : null}
      </Label>
      <select
        aria-label={label}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1.5 h-9 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px] text-[#374151]"
      >
        {options.map((opt) => (
          <option key={`${opt.value}-${opt.label}`} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
}

type CreateFormValues = {
  label: string;
  copy_from_year_id: string;
  start_date: string;
  end_date: string;
  semester_count: string;
  admission_intake_opens: string;
};

function renderCreateField(
  field: AcademicYearCreateFormField,
  form: ReturnType<typeof useForm<CreateFormValues>>,
  copyOptions: AcademicYearCreateFormOption[],
  semesterOptions: AcademicYearCreateFormOption[],
) {
  const key = field.key as keyof CreateFormValues;
  if (field.field_type === "select" && field.key === "copy_from_year_id") {
    return (
      <SelectField
        key={field.key}
        label={field.label}
        value={form.watch("copy_from_year_id")}
        onChange={(v) => form.setValue("copy_from_year_id", v)}
        options={copyOptions}
      />
    );
  }
  if (field.field_type === "select" && field.key === "semester_count") {
    return (
      <SelectField
        key={field.key}
        label={field.label}
        value={form.watch("semester_count")}
        onChange={(v) => form.setValue("semester_count", v)}
        options={semesterOptions}
      />
    );
  }
  if (field.field_type === "date") {
    return (
      <div key={field.key}>
        <Label className="text-[13px] text-[#374151]">
          {field.label}
          {field.required ? <span className="text-[#dc2626]"> *</span> : null}
        </Label>
        <Input type="date" className="mt-1.5 h-9" {...form.register(key)} />
      </div>
    );
  }
  return (
    <div key={field.key}>
      <Label className="text-[13px] text-[#374151]">
        {field.label}
        {field.required ? <span className="text-[#dc2626]"> *</span> : null}
      </Label>
      <Input className="mt-1.5 h-9" {...form.register(key, { required: field.required })} />
    </div>
  );
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

export function AcademicYearManagementDashboard() {
  const [page, setPage] = useState(1);
  const { data, isLoading, isError, error, refetch } = useAcademicYearManagementPage(page);
  const createYear = useCreateAcademicYearManagement();
  const closeYear = useCloseCurrentAcademicYear();
  const saveRules = useSaveAcademicYearManagementRules();

  const form = useForm<CreateFormValues>({
    defaultValues: {
      label: "",
      copy_from_year_id: "",
      start_date: "",
      end_date: "",
      semester_count: "2",
      admission_intake_opens: "",
    },
  });

  const [rulesState, setRulesState] = useState<Record<string, boolean>>({});

  useEffect(() => {
    if (!data?.rules) return;
    const next: Record<string, boolean> = {};
    for (const rule of data.rules) {
      next[rule.key] = rule.enabled;
    }
    setRulesState(next);
  }, [data?.rules]);

  const persistRules = (key: string, enabled: boolean) => {
    const next = {
      ...rulesState,
      [key]: enabled,
    };
    setRulesState(next);
    saveRules.mutate({
      only_one_current_year: next.only_one_current_year ?? true,
      lock_closed_years: next.lock_closed_years ?? true,
    });
  };

  return (
    <div className="space-y-5" data-figma-frame="69:139876">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Academic Year Management"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">
            {data?.page_subtitle ?? "Create, open and close academic years"}
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap items-center gap-2">
          <Link
            href={data?.semesters_button_href ?? "/college-admin/academics/semester-management"}
            className="inline-flex h-9 items-center rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] shadow-[0_1px_2px_rgba(15,23,42,0.04)] hover:bg-[#f9fafb]"
          >
            {data?.semesters_button_label ?? "Semesters"}
          </Link>
          <button
            type="button"
            disabled={!data?.close_current_year_enabled || closeYear.isPending}
            onClick={() => closeYear.mutate()}
            className="inline-flex h-9 items-center gap-1.5 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] shadow-[0_1px_2px_rgba(15,23,42,0.04)] hover:bg-[#f9fafb] disabled:cursor-not-allowed disabled:opacity-50"
          >
            <LockIcon className="size-3.5 shrink-0" aria-hidden />
            {data?.close_current_year_label ?? "Close current year"}
          </button>
          <button
            type="button"
            onClick={() => {
              const el = document.getElementById("create-academic-year-form");
              el?.scrollIntoView({ behavior: "smooth", block: "start" });
            }}
            className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white shadow-[0_1px_2px_rgba(36,93,216,0.25)] hover:bg-[#1f4fb8]"
          >
            <PlusIcon className="size-3.5 shrink-0" aria-hidden />
            {data?.new_academic_year_label ?? "New academic year"}
          </button>
        </div>
      </div>

      {data?.sub_nav?.length ? <YearsSemestersSubNav items={data.sub_nav} /> : null}

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_360px]">
              <div className="space-y-5">
                <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                  <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                    <h3 className="text-[14px] font-semibold text-[#111827]">{data.academic_years_table_title}</h3>
                  </div>
                  {data.academic_years.length ? (
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
                          {data.academic_years.map((row) => (
                            <tr key={row.year_id} className="hover:bg-[#f9fafb]">
                              <td className="px-5 py-3 font-medium text-[#111827]">{row.label}</td>
                              <td className="py-3 pr-3 text-[#374151]">{row.start_label}</td>
                              <td className="py-3 pr-3 text-[#374151]">{row.end_label}</td>
                              <td className="py-3 pr-3 tabular-nums text-[#374151]">
                                {row.student_count.toLocaleString("en-IN")}
                              </td>
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
                  <div className="flex flex-wrap items-center justify-between gap-3 border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
                    <span>{data.academic_year_count_label}</span>
                    {data.total_pages > 1 ? (
                      <div className="flex items-center gap-1">
                        {Array.from({ length: data.total_pages }, (_, i) => i + 1).map((p) => (
                          <button
                            key={p}
                            type="button"
                            onClick={() => setPage(p)}
                            className={cn(
                              "inline-flex size-8 items-center justify-center rounded-md border text-xs font-medium transition-colors",
                              p === data.page
                                ? "border-[#245dd8] bg-[#eff6ff] text-[#245dd8] shadow-[0_0_0_1px_rgba(36,93,216,0.15)]"
                                : "border-[#e5e7eb] bg-white text-[#6b7280] hover:border-[#dce3ec] hover:bg-[#f9fafb]",
                            )}
                          >
                            {p}
                          </button>
                        ))}
                      </div>
                    ) : null}
                  </div>
                </section>

                <section
                  id="create-academic-year-form"
                  className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]"
                >
                  <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                    <h3 className="text-[14px] font-semibold text-[#111827]">{data.create_section_title}</h3>
                  </div>
                  <form
                    className="sm:grid sm:grid-cols-2 sm:gap-4"
                    onSubmit={form.handleSubmit((values) => {
                      createYear.mutate(
                        {
                          label: values.label.trim(),
                          copy_from_year_id: values.copy_from_year_id || null,
                          start_date: values.start_date || null,
                          end_date: values.end_date || null,
                          semester_count: Number(values.semester_count || "2"),
                          admission_intake_opens: values.admission_intake_opens || null,
                        },
                        {
                          onSuccess: () => {
                            form.reset({
                              label: "",
                              copy_from_year_id: "",
                              start_date: "",
                              end_date: "",
                              semester_count: "2",
                              admission_intake_opens: "",
                            });
                          },
                        },
                      );
                    })}
                  >
                    <div className="grid gap-4 px-5 pt-4 sm:col-span-2 sm:grid-cols-2">
                      {data.create_fields.map((field) =>
                        renderCreateField(field, form, data.copy_from_options, data.semester_count_options),
                      )}
                    </div>
                    <div className="mt-5 flex flex-col gap-3 border-t border-[#f1f5f9] bg-[#fafbfc]/60 px-5 py-4 sm:col-span-2 sm:flex-row sm:items-center sm:justify-between">
                      <p className="text-[12px] leading-relaxed text-[#6b7280]">{data.create_form_note}</p>
                      <div className="flex shrink-0 flex-wrap items-center gap-2">
                        <button
                          type="button"
                          onClick={() => form.reset()}
                          className="inline-flex h-9 min-w-[5.5rem] items-center justify-center rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] shadow-[0_1px_2px_rgba(15,23,42,0.04)] hover:bg-[#f9fafb]"
                        >
                          {data.cancel_label}
                        </button>
                        <button
                          type="submit"
                          disabled={createYear.isPending}
                          className="inline-flex h-9 items-center justify-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white shadow-[0_1px_2px_rgba(36,93,216,0.25)] hover:bg-[#1f4fb8] disabled:cursor-not-allowed disabled:opacity-50"
                        >
                          <CalendarDaysIcon className="size-3.5 shrink-0" aria-hidden />
                          {data.create_submit_label}
                        </button>
                      </div>
                    </div>
                  </form>
                </section>
              </div>

              <div className="space-y-5">
                <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                  <h3 className="mb-3 text-[14px] font-semibold text-[#111827]">{data.checklist_title}</h3>
                  <ul className="space-y-3 border-l border-[#e5e7eb] pl-4">
                    {data.checklist_items.map((item) => (
                      <li key={item.key} className="relative pl-2">
                        <span
                          className={cn(
                            "absolute -left-[21px] top-1.5 size-2.5 rounded-full ring-4 ring-white",
                            item.completed ? "bg-[#10b981]" : "bg-[#3b82f6]",
                          )}
                        />
                        <p className="text-[13px] font-medium text-[#111827]">{item.title}</p>
                        {item.detail ? <p className="text-[12px] text-[#6b7280]">{item.detail}</p> : null}
                      </li>
                    ))}
                  </ul>
                </section>

                <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white px-5 py-2 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                  <h3 className="border-b border-[#f1f5f9] py-3.5 text-[14px] font-semibold text-[#111827]">
                    {data.rules_section_title}
                  </h3>
                  <div className="divide-y divide-[#f1f5f9]">
                    {data.rules.map((rule) => (
                      <RuleToggle
                        key={rule.key}
                        rule={rule}
                        checked={rulesState[rule.key] ?? rule.enabled}
                        onChange={(next) => persistRules(rule.key, next)}
                      />
                    ))}
                  </div>
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