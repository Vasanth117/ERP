"use client";

import Link from "next/link";
import { useMemo } from "react";
import { useSearchParams } from "next/navigation";

import { CalendarIcon } from "@/components/icons/erp/generated/calendar";
import { MailIcon } from "@/components/icons/erp/generated/mail";
import { PencilIcon } from "@/components/icons/erp/generated/pencil";
import { PhoneIcon } from "@/components/icons/erp/generated/phone";
import { PrinterIcon } from "@/components/icons/erp/generated/printer";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useFacultyTimetablePage } from "@/features/college-admin/hooks/use-faculty-timetable";
import { cn } from "@/lib/utils";

function Badge({ label, tone }: { label: string; tone: string }) {
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


export function FacultyTimetableDashboard() {
  const searchParams = useSearchParams();
  const recordId = useMemo(
    () => searchParams.get("record_id") ?? searchParams.get("id") ?? undefined,
    [searchParams],
  );

  const pageQuery = useFacultyTimetablePage(recordId);
  const data = pageQuery.data;

  return (
    <div className="space-y-5" data-figma-frame="159:5488">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Faculty Timetable"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">{data?.context_line ?? data?.page_subtitle}</p>
        </div>
        {!data?.requires_record ? (
          <div className="flex shrink-0 flex-wrap gap-2">
            <button
              type="button"
              onClick={() => window.print()}
              className="inline-flex h-9 items-center gap-1.5 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb]"
            >
              <PrinterIcon className="size-3.5" aria-hidden />
              {data?.print_label ?? "Print"}
            </button>
            {data?.edit_slots_href ? (
              <Link
                href={data.edit_slots_href}
                className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
              >
                <PencilIcon className="size-3.5" aria-hidden />
                {data.edit_slots_label}
              </Link>
            ) : null}
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
          <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
            <h3 className="text-[14px] font-semibold text-[#111827]">
              {data.select_faculty_title ?? "Select a faculty member"}
            </h3>
            <p className="mt-1 text-sm text-[#6b7280]">{data.select_faculty_hint}</p>
            {data.picker_rows.length ? (
              <ul className="mt-4 divide-y divide-[#f1f5f9] rounded-lg border border-[#e8ecf2]">
                {data.picker_rows.map((row) => (
                  <li key={row.record_id}>
                    <Link
                      href={row.timetable_href}
                      className="flex items-center justify-between gap-4 px-4 py-3 text-[13px] hover:bg-[#f9fafb]"
                    >
                      <span className="font-medium text-[#111827]">{row.faculty_name}</span>
                      <span className="font-mono text-[#6b7280]">{row.employee_id_label}</span>
                    </Link>
                  </li>
                ))}
              </ul>
            ) : null}
            {data.faculty_directory_href ? (
              <Link
                href={data.faculty_directory_href}
                className="mt-4 inline-flex text-sm font-medium text-[#245dd8] hover:underline"
              >
                {data.faculty_directory_label} →
              </Link>
            ) : null}
          </section>
        ) : data ? (
          <>
            <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
                <div
                  className="flex size-14 shrink-0 items-center justify-center rounded-full bg-[#eff6ff] text-[16px] font-semibold text-[#245dd8]"
                  aria-hidden
                >
                  {data.profile_initials}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="text-[18px] font-bold text-[#111827]">{data.profile_name}</h3>
                    {data.profile_badges.map((badge) => (
                      <Badge key={badge.key} label={badge.label} tone={badge.tone} />
                    ))}
                  </div>
                  <p className="mt-1 text-[13px] text-[#6b7280]">{data.profile_summary_line}</p>
                  <div className="mt-3 flex flex-wrap gap-x-5 gap-y-2 text-[12px] text-[#374151]">
                    <span className="inline-flex items-center gap-1.5">
                      <MailIcon className="size-3.5 text-[#9ca3af]" aria-hidden />
                      {data.email_display}
                    </span>
                    <span className="inline-flex items-center gap-1.5">
                      <PhoneIcon className="size-3.5 text-[#9ca3af]" aria-hidden />
                      {data.phone_display}
                    </span>
                    <span className="inline-flex items-center gap-1.5">
                      <CalendarIcon className="size-3.5 text-[#9ca3af]" aria-hidden />
                      {data.joined_label}
                    </span>
                  </div>
                </div>
              </div>
            </section>

            <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.weekly_section_title}</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[640px] text-left text-[13px]">
                  <thead className="border-b border-[#f1f5f9] bg-[#f9fafb] text-[11px] font-semibold text-[#6b7280]">
                    <tr>
                      {data.column_headers.map((h) => (
                        <th key={h} className="px-3 py-2.5 font-semibold whitespace-nowrap">
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#f1f5f9]">
                    {data.day_rows.map((day) => (
                      <tr key={day.day_key}>
                        <td className="px-3 py-3 font-medium text-[#111827]">{day.day_label}</td>
                        {day.cells.map((cell, idx) => (
                          <td
                            key={`${day.day_key}-${idx}`}
                            className={cn(
                              "px-3 py-3 text-[#374151]",
                              cell.is_empty ? "text-center text-[#d1d5db]" : undefined,
                            )}
                          >
                            {cell.label}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">{data.timetable_footer_label}</p>
            </section>

          </>
        ) : null}
      </QueryState>
    </div>
  );
}