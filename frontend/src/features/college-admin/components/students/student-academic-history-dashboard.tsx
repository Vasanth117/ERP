"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useCallback, useMemo } from "react";

import { CalendarIcon } from "@/components/icons/erp/generated/calendar";
import { ChevronLeftIcon } from "@/components/icons/erp/generated/chevron-left";
import { MailIcon } from "@/components/icons/erp/generated/mail";
import { PhoneIcon } from "@/components/icons/erp/generated/phone";
import { CollegeAdminDownload } from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { StudentsTabHeader } from "@/features/college-admin/components/students/students-tab-header";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useStudentAcademicHistoryPage } from "@/features/college-admin/hooks/use-student-academic-history-page";
import { cn } from "@/lib/utils";

function Badge({ label, tone }: { label: string; tone: string }) {
  const styles: Record<string, string> = {
    success: "bg-[#ecfdf5] text-[#047857]",
    warning: "bg-[#fff7ed] text-[#c2410c]",
    error: "bg-[#fef2f2] text-[#b91c1c]",
    info: "bg-[#eff6ff] text-[#1d4ed8]",
    muted: "bg-[#f3f4f6] text-[#6b7280]",
  };
  const key = tone in styles ? tone : "muted";
  return (
    <span className={cn("rounded-full px-2.5 py-0.5 text-[11px] font-medium", styles[key])}>{label}</span>
  );
}

function StatusPill({ label, tone }: { label: string; tone: string }) {
  const styles: Record<string, string> = {
    success: "bg-[#ecfdf5] text-[#047857]",
    warning: "bg-[#fff7ed] text-[#c2410c]",
    error: "bg-[#fef2f2] text-[#b91c1c]",
    info: "bg-[#eff6ff] text-[#1d4ed8]",
    muted: "bg-[#f3f4f6] text-[#6b7280]",
  };
  const dot: Record<string, string> = {
    success: "bg-[#10b981]",
    warning: "bg-[#f97316]",
    error: "bg-[#ef4444]",
    info: "bg-[#3b82f6]",
    muted: "bg-[#9ca3af]",
  };
  const key = tone in styles ? tone : "muted";
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-medium",
        styles[key],
      )}
    >
      <span className={cn("size-1.5 rounded-full", dot[key])} />
      {label}
    </span>
  );
}

function RecordChangesTimeline({
  title,
  steps,
}: {
  title: string;
  steps: { key: string; label: string; date_label: string; tone: string }[];
}) {
  return (
    <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
      <div className="border-b border-[#f1f5f9] px-5 py-3.5">
        <h3 className="text-[14px] font-semibold text-[#111827]">{title}</h3>
      </div>
      {steps.length ? (
        <ol className="space-y-0 px-5 py-4">
          {steps.map((step, index) => (
            <li key={step.key} className="relative flex gap-3 pb-5 last:pb-0">
              {index < steps.length - 1 ? (
                <span
                  className="absolute left-[5px] top-3 h-[calc(100%-4px)] w-px bg-[#e5e7eb]"
                  aria-hidden
                />
              ) : null}
              <span
                className={cn(
                  "relative z-[1] mt-1 size-2.5 shrink-0 rounded-full ring-4 ring-white",
                  step.tone === "success"
                    ? "bg-[#10b981]"
                    : step.tone === "warning"
                      ? "bg-[#f97316]"
                      : step.tone === "info"
                        ? "bg-[#3b82f6]"
                        : "bg-[#d1d5db]",
                )}
              />
              <div>
                <p className="text-[13px] font-medium text-[#111827]">{step.label}</p>
                <p className="text-[12px] text-[#6b7280]">{step.date_label}</p>
              </div>
            </li>
          ))}
        </ol>
      ) : (
        <p className="px-5 py-8 text-sm text-[#9ca3af]">No record changes yet.</p>
      )}
    </section>
  );
}


export function StudentAcademicHistoryDashboard() {
  const searchParams = useSearchParams();
  const recordId = useMemo(() => searchParams.get("id") ?? searchParams.get("record_id") ?? "", [searchParams]);

  const { data, isLoading, isError, error, refetch } = useStudentAcademicHistoryPage(recordId || null);

  const handleExport = useCallback(() => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `student-academic-history-${data.selected_record_id || "export"}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data]);

  if (!recordId) {
    return (
      <div className="space-y-5" data-figma-frame="158:7002">
        <StudentsTabHeader
          title="Student Academic History"
          subtitle="Semester results and changes of record"
        />
        <div className="rounded-xl border border-dashed border-[#dce3ec] bg-[#f9fafb] px-5 py-10 text-center">
          <p className="text-sm text-[#6b7280]">
            Choose a student to view semester results, grades, and record changes.
          </p>
          <div className="mt-4 flex flex-wrap items-center justify-center gap-2">
            <Link
              href="/college-admin/students/all-students-list"
              className="inline-flex h-9 items-center rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
            >
              Browse all students
            </Link>
            <Link
              href="/college-admin/students/student-details"
              className="inline-flex h-9 items-center rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb]"
            >
              Open student details
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-5" data-figma-frame="158:7002">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex min-w-0 items-start gap-3">
          <Link
            href={data?.back_href ?? "/college-admin/students/all-students-list"}
            className="mt-0.5 inline-flex size-8 shrink-0 items-center justify-center rounded-md border border-[#dce3ec] text-[#6b7280] hover:bg-[#f9fafb]"
            aria-label={data?.back_label ?? "Back"}
          >
            <ChevronLeftIcon className="size-4" />
          </Link>
          <StudentsTabHeader
            title={data?.page_title ?? "Student Academic History"}
            subtitle={data?.page_subtitle ?? "Semester results and changes of record"}
          />
        </div>
        <button
          type="button"
          className="inline-flex h-9 shrink-0 items-center gap-1.5 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb] disabled:opacity-50"
          disabled={!data}
          onClick={handleExport}
        >
          <CollegeAdminDownload className="size-3.5" aria-hidden />
          {data?.export_label ?? "Export"}
        </button>
      </div>

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <>
            <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white px-5 py-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-start">
                <span className="flex size-14 shrink-0 items-center justify-center rounded-full bg-[#eff6ff] text-lg font-semibold text-[#245dd8]">
                  {data.profile_initials}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="text-[18px] font-semibold text-[#111827]">{data.profile_name}</h3>
                    {data.profile_badges.map((badge) => (
                      <Badge key={badge.key} label={badge.label} tone={badge.tone} />
                    ))}
                  </div>
                  <p className="mt-1 text-[13px] text-[#6b7280]">{data.profile_summary_line}</p>
                  <div className="mt-3 flex flex-wrap gap-x-5 gap-y-2 text-[13px] text-[#374151]">
                    <span className="inline-flex items-center gap-1.5">
                      <MailIcon className="size-3.5 text-[#9ca3af]" aria-hidden />
                      {data.email}
                    </span>
                    <span className="inline-flex items-center gap-1.5">
                      <PhoneIcon className="size-3.5 text-[#9ca3af]" aria-hidden />
                      {data.phone}
                    </span>
                    <span className="inline-flex items-center gap-1.5">
                      <CalendarIcon className="size-3.5 text-[#9ca3af]" aria-hidden />
                      {data.admitted_label}
                    </span>
                  </div>
                </div>
              </div>
            </section>

            <div className="grid grid-cols-1 gap-5 lg:grid-cols-[1fr_300px]">
              <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                  <h3 className="text-[14px] font-semibold text-[#111827]">{data.semester_record_section_title}</h3>
                </div>
                {data.semester_rows.length ? (
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[36rem] text-left text-[13px]">
                      <thead>
                        <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                          {data.semester_table_headers.map((header, index) => (
                            <th
                              key={header}
                              className={cn(
                                "pb-3 font-medium",
                                index === 0 ? "px-5 pt-4" : "pr-3 pt-4",
                                index === data.semester_table_headers.length - 1 ? "pr-5" : "",
                              )}
                            >
                              {header}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#f1f5f9]">
                        {data.semester_rows.map((row) => (
                          <tr key={row.term_key} className="text-[#374151]">
                            <td className="px-5 py-3 font-medium text-[#111827]">{row.semester_label}</td>
                            <td className="py-3 pr-3">{row.year_label}</td>
                            <td className="py-3 pr-3 tabular-nums">{row.sgpa_label}</td>
                            <td className="py-3 pr-3 tabular-nums">{row.credits_label}</td>
                            <td className="py-3 pr-3">
                              <StatusPill label={row.result_label} tone={row.result_tone} />
                            </td>
                            <td className="py-3 pr-5 tabular-nums">{row.attendance_label}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="px-5 py-8 text-sm text-[#9ca3af]">No semester results recorded yet.</p>
                )}
                <div className="border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
                  {data.semester_footer_label}
                </div>
              </section>

              <RecordChangesTimeline title={data.record_changes_section_title} steps={data.record_change_steps} />
            </div>

          </>
        ) : null}
      </QueryState>
    </div>
  );
}