"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useMemo } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { ChevronLeftIcon } from "@/components/icons/erp/generated/chevron-left";
import { YearsSemestersSubNav } from "@/features/college-admin/components/academics/years-semesters-sub-nav";
import {
  CollegeAdminPrimaryButton,
  CollegeAdminSecondaryButton,
} from "@/features/college-admin/components/ui/college-admin-action-button";
import {
  CollegeAdminPanelChromeFooter,
  CollegeAdminPanelChromeHeader,
  CollegeAdminPanelShell,
  CollegeAdminSidePanel,
} from "@/features/college-admin/components/ui/dashboard-panel-ui";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useSaveSemesterManagementSettings,
  useSemesterManagementPage,
} from "@/features/college-admin/hooks/use-semester-management";
import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

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

function StatusPill({ label, tone }: { label: string; tone: string }) {
  const styles: Record<string, string> = {
    success: "bg-[#ecfdf5] text-[#047857]",
    warning: "bg-[#fff7ed] text-[#c2410c]",
    info: "bg-[#eff6ff] text-[#1d4ed8]",
    muted: "bg-[#f3f4f6] text-[#6b7280]",
  };
  const key = tone in styles ? tone : "muted";
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-medium", styles[key])}>
      <span className={cn("size-1.5 rounded-full", key === "success" ? "bg-[#10b981]" : key === "warning" ? "bg-[#f97316]" : "bg-[#9ca3af]")} />
      {label}
    </span>
  );
}

export function SemesterDetailsDashboard() {
  const searchParams = useSearchParams();
  const termId = useMemo(() => searchParams.get("term_id") ?? "", [searchParams]);
  const yearId = useMemo(() => searchParams.get("academic_year_id") ?? undefined, [searchParams]);

  const { data, isLoading, isError, error, refetch } = useSemesterManagementPage({
    academic_year_id: yearId,
    term_id: termId || undefined,
  });
  const saveSettings = useSaveSemesterManagementSettings();

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

  useEffect(() => {
    const defaults = data?.settings_form;
    if (!defaults) return;
    form.reset({
      teaching_starts: toInputDate(defaults.teaching_starts),
      last_instruction_day: toInputDate(defaults.last_instruction_day),
      mid_semester_exam_date: toInputDate(defaults.mid_semester_exam_date),
      end_semester_exam_date: toInputDate(defaults.end_semester_exam_date),
      course_registration_opens: toInputDate(defaults.course_registration_opens),
      add_drop_deadline: toInputDate(defaults.add_drop_deadline),
    });
  }, [data?.settings_form, form]);

  if (!termId) {
    return (
      <p className="rounded-xl border border-[#e8ecf2] bg-white p-6 text-sm text-[#6b7280]">
        Open a semester from{" "}
        <Link href="/college-admin/academics/semester-management" className="font-medium text-[#245dd8] hover:underline">
          Semester management
        </Link>
        .
      </p>
    );
  }

  const selectedRow = data?.semester_rows.find((r) => r.term_id === termId);

  return (
    <div className="space-y-5">
      {data?.sub_nav?.length ? <YearsSemestersSubNav items={data.sub_nav} /> : null}

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data && data.settings_form ? (
          <>
            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
              <div className="flex min-w-0 items-start gap-3">
                <Link
                  href="/college-admin/academics/semester-management"
                  className="inline-flex size-9 shrink-0 items-center justify-center rounded-md border border-[#e8ecf2] bg-white hover:bg-[#f9fafb]"
                  aria-label="Back"
                >
                  <ChevronLeftIcon className="size-5" />
                </Link>
                <div>
                  <CardTitle row={selectedRow} fallback={data.settings_panel_title.replace(" settings", "")} />
                  <p className="mt-1 text-[14px] text-[#6b7280]">
                    {data.selected_academic_year_label} · Semester details
                  </p>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_360px]">
              <CollegeAdminPanelShell>
                <CollegeAdminPanelChromeHeader title={data.settings_panel_title} />
                <form
                  onSubmit={form.handleSubmit((values) => {
                    saveSettings.mutate(
                      {
                        term_id: termId,
                        settings: {
                          teaching_starts: values.teaching_starts || null,
                          last_instruction_day: values.last_instruction_day || null,
                          mid_semester_exam_date: values.mid_semester_exam_date || null,
                          end_semester_exam_date: values.end_semester_exam_date || null,
                          course_registration_opens: values.course_registration_opens || null,
                          add_drop_deadline: values.add_drop_deadline || null,
                        },
                      },
                      { onSuccess: () => toast.success("Semester settings saved") },
                    );
                  })}
                >
                  <div className="grid gap-4 px-5 py-4 sm:grid-cols-2">
                    {data.settings_field_meta.map((field) => (
                      <div key={field.key}>
                        <Label className="text-[13px] font-medium text-[#374151]">
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
                  </div>
                  <CollegeAdminPanelChromeFooter className="flex-col gap-3 sm:flex-row sm:items-center">
                    <p className="text-[12px] font-normal text-[#64748b]">{data.settings_form_note}</p>
                    <div className="flex shrink-0 gap-2 sm:ml-auto">
                      <CollegeAdminSecondaryButton type="button" onClick={() => form.reset()}>
                        {data.cancel_label}
                      </CollegeAdminSecondaryButton>
                      <CollegeAdminPrimaryButton type="submit" disabled={saveSettings.isPending}>
                        {data.save_label}
                      </CollegeAdminPrimaryButton>
                    </div>
                  </CollegeAdminPanelChromeFooter>
                </form>
              </CollegeAdminPanelShell>

              <aside className="space-y-5">
                <ProgressCard data={data} />
                <LinkedCard data={data} />
              </aside>
            </div>
          </>
        ) : null}
      </QueryState>
    </div>
  );
}

function CardTitle({
  row,
  fallback,
}: {
  row: { label: string; status_label: string; status_tone: string } | undefined;
  fallback: string;
}) {
  if (!row) return <h2 className="text-[22px] font-bold text-[#111827]">{fallback}</h2>;
  return (
    <div className="flex flex-wrap items-center gap-2">
      <h2 className="text-[22px] font-bold text-[#111827]">{row.label}</h2>
      <StatusPill label={row.status_label} tone={row.status_tone} />
    </div>
  );
}

function ProgressCard({ data }: { data: NonNullable<ReturnType<typeof useSemesterManagementPage>["data"]> }) {
  return (
    <CollegeAdminSidePanel title={data.progress_section_title}>
      <ul className="space-y-4">
        {data.progress_items.map((item) => (
          <li key={item.key}>
            <div className="mb-1.5 flex justify-between text-[13px]">
              <span className="font-medium text-[#111827]">{item.label}</span>
              <span className="tabular-nums text-[#64748b]">{item.progress_percent}%</span>
            </div>
            <div className="h-1.5 overflow-hidden rounded-full bg-[#e8ecf2]">
              <div className="h-full rounded-full bg-[#245dd8]" style={{ width: `${item.progress_percent}%` }} />
            </div>
          </li>
        ))}
      </ul>
    </CollegeAdminSidePanel>
  );
}

function LinkedCard({ data }: { data: NonNullable<ReturnType<typeof useSemesterManagementPage>["data"]> }) {
  return (
    <CollegeAdminSidePanel title={data.linked_section_title}>
      <ul className="divide-y divide-[#f1f5f9]">
        {data.linked_items.map((item) => (
          <li key={item.key} className="flex items-start justify-between gap-3 py-3 first:pt-0 last:pb-0">
            <div className="min-w-0">
              <p className="text-[13px] font-medium text-[#111827]">{item.title}</p>
              <p className="text-[12px] text-[#64748b]">{item.subtitle}</p>
            </div>
            <StatusPill label={item.status_label} tone={item.status_tone} />
          </li>
        ))}
      </ul>
    </CollegeAdminSidePanel>
  );
}