"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useMemo } from "react";

import { CalendarIcon } from "@/components/icons/erp/generated/calendar";
import { ChevronLeftIcon } from "@/components/icons/erp/generated/chevron-left";
import { ClockIcon } from "@/components/icons/erp/generated/clock";
import { MailIcon } from "@/components/icons/erp/generated/mail";
import { PencilIcon } from "@/components/icons/erp/generated/pencil";
import { PhoneIcon } from "@/components/icons/erp/generated/phone";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useStudentDetailsPage } from "@/features/college-admin/hooks/use-student-details-page";
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
    <span className={cn("inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-medium", styles[key])}>
      <span className={cn("size-1.5 rounded-full", dot[key])} />
      {label}
    </span>
  );
}

function SectionCard({
  title,
  children,
  footer,
}: {
  title: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
}) {
  return (
    <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
      <div className="border-b border-[#f1f5f9] px-5 py-3.5">
        <h3 className="text-[14px] font-semibold text-[#111827]">{title}</h3>
      </div>
      <div className="px-5 py-4">{children}</div>
      {footer ? (
        <div className="border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">{footer}</div>
      ) : null}
    </section>
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

export function StudentDetailsDashboard() {
  const searchParams = useSearchParams();
  const recordId = useMemo(() => searchParams.get("id") ?? searchParams.get("record_id") ?? "", [searchParams]);

  const { data, isLoading, isError, error, refetch } = useStudentDetailsPage(recordId || null);

  if (!recordId) {
    return (
      <div className="rounded-xl border border-[#e8ecf2] bg-white p-6 text-sm text-[#6b7280]">
        Select a student from{" "}
        <Link href="/college-admin/students/all-students-list" className="font-medium text-[#245dd8] hover:underline">
          All students
        </Link>
        .
      </div>
    );
  }

  return (
    <div className="space-y-5" data-figma-frame="158:2564">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="flex min-w-0 items-start gap-3">
          <Link
            href={data?.back_href ?? "/college-admin/students/all-students-list"}
            className="mt-1 inline-flex size-8 shrink-0 items-center justify-center rounded-md border border-[#dce3ec] text-[#6b7280] hover:bg-[#f9fafb]"
            aria-label={data?.back_label ?? "Back"}
          >
            <ChevronLeftIcon className="size-4" />
          </Link>
          <div>
            <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
              {data?.page_title ?? "Student Details"}
            </h2>
            <p className="mt-1 text-[14px] text-[#6b7280]">{data?.page_subtitle ?? "—"}</p>
          </div>
        </div>
        {data ? (
          <div className="flex shrink-0 flex-wrap gap-2">
            <Link
              href={data.edit_profile_href}
              className="inline-flex h-9 items-center gap-1.5 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb]"
            >
              <PencilIcon className="size-3.5" aria-hidden />
              {data.edit_profile_label}
            </Link>
            <Link
              href={data.academic_history_href}
              className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
            >
              <ClockIcon className="size-3.5" aria-hidden />
              {data.academic_history_label}
            </Link>
          </div>
        ) : null}
      </div>

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
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

            <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_360px]">
              <div className="space-y-5">
                <SectionCard title={data.enrollment_section_title}>
                  <table className="w-full text-[13px]">
                    <tbody className="divide-y divide-[#f1f5f9]">
                      {data.enrollment_rows.map((row) => (
                        <tr key={row.key}>
                          <td className="py-2.5 pr-4 font-medium text-[#6b7280]">{row.label}</td>
                          <td className="py-2.5 text-right font-medium text-[#111827]">{row.value}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </SectionCard>

                <SectionCard title={data.documents_section_title} footer={data.documents_footer_label}>
                  {data.document_rows.length ? (
                    <div className="overflow-x-auto">
                      <table className="w-full min-w-[28rem] text-left text-[13px]">
                        <thead>
                          <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                            {data.documents_table_headers.map((header) => (
                              <th key={header} className="pb-3 pr-3 font-medium last:pr-0">
                                {header}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-[#f1f5f9]">
                          {data.document_rows.map((row) => (
                            <tr key={row.document_key}>
                              <td className="py-3 pr-3 font-medium text-[#111827]">{row.document_label}</td>
                              <td className="py-3 pr-3 text-[#374151]">{row.uploaded_label}</td>
                              <td className="py-3 pr-3">
                                <StatusPill label={row.status_label} tone={row.status_tone} />
                              </td>
                              <td className="py-3 text-[#374151]">{row.verified_by_label}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="text-sm text-[#9ca3af]">No documents on file for this student.</p>
                  )}
                </SectionCard>
              </div>

              <div className="space-y-5">
                <SectionCard title={data.contact_section_title}>
                  <dl className="space-y-3 text-[13px]">
                    {data.contact_rows.map((row) => (
                      <div key={row.key}>
                        <dt className="text-[#6b7280]">{row.label}</dt>
                        <dd className="mt-0.5 font-medium text-[#111827]">{row.value}</dd>
                      </div>
                    ))}
                  </dl>
                </SectionCard>

                <SectionCard title={data.standing_section_title}>
                  <dl className="space-y-3.5 text-[13px]">
                    {data.standing_fields.map((field) => (
                      <div key={field.key} className="flex items-center justify-between gap-3">
                        <dt className="text-[#6b7280]">{field.label}</dt>
                        <dd
                          className={cn(
                            "font-semibold tabular-nums text-[#111827]",
                            field.value_tone === "success" && "text-[#047857]",
                            field.value_tone === "warning" && "text-[#c2410c]",
                            field.value_tone === "error" && "text-[#b91c1c]",
                          )}
                        >
                          {field.value}
                        </dd>
                      </div>
                    ))}
                  </dl>
                </SectionCard>
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