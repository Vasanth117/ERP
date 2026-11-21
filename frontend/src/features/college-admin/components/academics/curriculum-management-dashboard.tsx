"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { CollegeAdminDownload } from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { CourseCurriculumSubNav } from "@/features/college-admin/components/academics/course-curriculum-sub-nav";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useCurriculumManagementPage } from "@/features/college-admin/hooks/use-course-curriculum";
import { cn } from "@/lib/utils";

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

export function CurriculumManagementDashboard() {
  const [programmeId, setProgrammeId] = useState<string | undefined>();
  const [semester, setSemester] = useState(4);

  const { data, isLoading, isError, error, refetch, isFetching } = useCurriculumManagementPage({
    programme_id: programmeId,
    semester,
  });

  useEffect(() => {
    if (data?.selected_programme_id) setProgrammeId(data.selected_programme_id);
    if (data?.selected_semester) setSemester(data.selected_semester);
  }, [data?.selected_programme_id, data?.selected_semester]);

  return (
    <div className="space-y-5" data-figma-frame="69:140845">
      {data?.sub_nav.length ? <CourseCurriculumSubNav items={data.sub_nav} /> : null}

      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold text-[#111827]">{data?.page_title ?? "Curriculum Management"}</h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">{data?.page_subtitle}</p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <Link
            href={data?.subjects_button_href ?? "/college-admin/academics/subject-management"}
            className="inline-flex h-9 items-center gap-1.5 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb]"
          >
            {data?.subjects_button_label ?? "Subjects"}
          </Link>
          <button
            type="button"
            disabled
            className="inline-flex h-9 items-center gap-1.5 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] opacity-60"
          >
            <CollegeAdminDownload className="size-3.5" />
            {data?.download_pdf_label ?? "Download PDF"}
          </button>
          <Link
            href={data?.edit_curriculum_href ?? "/college-admin/academics/course-configuration?mode=create"}
            className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
          >
            {data?.edit_curriculum_label ?? "Edit curriculum"}
          </Link>
        </div>
      </div>

      {data?.programme_options.length ? (
        <select
          aria-label="Programme"
          value={programmeId ?? ""}
          onChange={(e) => setProgrammeId(e.target.value)}
          className="h-9 max-w-md rounded-md border border-[#dce3ec] bg-white px-3 text-[13px]"
        >
          {data.programme_options.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      ) : null}

      {data?.semester_tabs.length ? (
        <div className="flex flex-wrap gap-1 rounded-lg border border-[#e8ecf2] bg-[#f9fafb] p-1">
          {data.semester_tabs.map((tab) => (
            <button
              key={tab.semester_number}
              type="button"
              onClick={() => setSemester(tab.semester_number)}
              className={cn(
                "rounded-md px-3 py-1.5 text-[13px] font-medium",
                tab.semester_number === semester || tab.is_selected
                  ? "bg-white text-[#245dd8] shadow-sm"
                  : "text-[#6b7280] hover:text-[#111827]",
              )}
            >
              {tab.tab_label}
            </button>
          ))}
        </div>
      ) : null}

      <QueryState isLoading={isLoading || isFetching} isError={isError} error={error} onRetry={() => void refetch()}>
        {data ? (
          <div className="grid gap-5 xl:grid-cols-3">
            <div className="space-y-4 xl:col-span-2">
              <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-sm">
                <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                  <h3 className="text-[14px] font-semibold text-[#111827]">{data.courses_panel_title}</h3>
                  <p className="text-[12px] text-[#6b7280]">{data.courses_panel_meta}</p>
                </div>
                {data.courses.length ? (
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[36rem] text-left text-[13px]">
                      <thead>
                        <tr className="text-[11px] uppercase tracking-wide text-[#9ca3af]">
                          {data.table_headers.map((h, i) => (
                            <th key={h} className={cn("pb-3 pt-4 font-medium", i === 0 ? "px-5" : "pr-3")}>
                              {h}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#f1f5f9]">
                        {data.courses.map((row) => (
                          <tr key={row.course_id} className="hover:bg-[#f9fafb]">
                            <td className="px-5 py-3">
                              <Link href={row.configuration_href} className="font-medium text-[#111827] hover:text-[#245dd8]">
                                <span className="font-mono text-[12px] text-[#6b7280]">{row.course_code}</span>
                                <span className="mt-0.5 block">{row.course_name}</span>
                              </Link>
                            </td>
                            <td className="py-3 pr-3">{row.type_label}</td>
                            <td className="py-3 pr-3 font-mono text-[12px]">{row.ltp_label}</td>
                            <td className="py-3 pr-3 tabular-nums">{row.credits_label}</td>
                            <td className="py-3 pr-5">
                              <StatusPill label={row.status_label} tone={row.status_tone} />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="px-5 py-8 text-sm text-[#9ca3af]">No courses for this semester.</p>
                )}
                <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
                  <span>{data.approval_footer_label}</span>
                  <Link href={data.version_history_href} className="font-medium text-[#245dd8] hover:underline">
                    {data.version_history_label}
                  </Link>
                </div>
              </section>
            </div>
            <div className="space-y-4">
              <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-sm">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.credits_panel_title}</h3>
                <ul className="mt-4 space-y-3">
                  {data.credit_categories.map((cat) => (
                    <li key={cat.category_key}>
                      <div className="flex justify-between text-[12px] text-[#374151]">
                        <span>{cat.category_label}</span>
                        <span className="tabular-nums font-medium">{cat.credits}</span>
                      </div>
                      {cat.share_pct != null ? (
                        <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-[#f1f5f9]">
                          <div className="h-full rounded-full bg-[#245dd8]" style={{ width: `${Math.min(100, cat.share_pct)}%` }} />
                        </div>
                      ) : null}
                    </li>
                  ))}
                </ul>
              </section>
              <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-sm">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.summary_panel_title}</h3>
                <dl className="mt-4 grid grid-cols-2 gap-3 text-[12px]">
                  {data.summary_fields.map((f) => (
                    <div key={f.key}>
                      <dt className="text-[#9ca3af]">{f.label}</dt>
                      <dd className="font-medium text-[#111827]">{f.value}</dd>
                    </div>
                  ))}
                </dl>
              </section>
            </div>
          </div>
        ) : null}
      </QueryState>
    </div>
  );
}