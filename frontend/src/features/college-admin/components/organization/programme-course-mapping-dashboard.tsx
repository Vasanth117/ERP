"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { LinkIcon } from "@/components/icons/erp/generated/link";
import { CollegeAdminDownload } from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useProgrammeCourseMappingPage } from "@/features/college-admin/hooks/use-programme-course-mapping";
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

function ActionPill({ label, tone }: { label: string; tone: string }) {
  const styles: Record<string, string> = {
    warning: "border-[#fed7aa] bg-[#fff7ed] text-[#c2410c]",
    info: "border-[#bfdbfe] bg-[#eff6ff] text-[#1d4ed8]",
  };
  const key = tone in styles ? tone : "info";
  return (
    <span className={cn("rounded-md border px-2.5 py-1 text-[11px] font-medium", styles[key])}>{label}</span>
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

export function ProgrammeCourseMappingDashboard() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialDept = searchParams.get("departmentId") ?? undefined;
  const [departmentId, setDepartmentId] = useState<string | undefined>(initialDept);
  const [moreOpen, setMoreOpen] = useState(false);

  useEffect(() => {
    if (initialDept) setDepartmentId(initialDept);
  }, [initialDept]);

  const { data, isLoading, isError, error, refetch, isFetching } = useProgrammeCourseMappingPage(departmentId);

  useEffect(() => {
    if (!departmentId && data?.selected_department_id) {
      setDepartmentId(data.selected_department_id);
    }
  }, [data, departmentId]);

  const selectDepartment = (id: string) => {
    setDepartmentId(id);
    setMoreOpen(false);
    router.replace(`/college-admin/organization/programme-course-mapping?departmentId=${id}`, { scroll: false });
  };

  const handleExport = useCallback(() => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `programme-course-mapping-${new Date(data.generated_at).toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data]);

  const progHeaders = data?.programmes_table_headers ?? ["Programme", "Level", "Duration", "Intake", "Regulation", "Status"];
  const serviceHeaders = data?.service_table_headers ?? ["Course", "Taught to", "Semester", "Students"];

  return (
    <div className="space-y-5" data-figma-frame="69:134275">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">
            {data?.page_title ?? "Programme & Course Mapping"}
          </h2>
          <p className="mt-1 text-[14px] text-[#6b7280]">
            {data?.page_subtitle ?? "Which programmes and courses each department offers and teaches"}
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <button
            type="button"
            className="inline-flex h-9 items-center gap-1.5 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb] disabled:opacity-50"
            onClick={handleExport}
            disabled={isLoading || !data}
          >
            <CollegeAdminDownload className="size-3.5" aria-hidden />
            {data?.export_label ?? "Export"}
          </button>
          <Link
            href={data?.map_programme_href ?? "/college-admin/academics/academic-configuration-dashboard"}
            className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
          >
            <LinkIcon className="size-3.5" aria-hidden />
            {data?.map_programme_label ?? "Map programme"}
          </Link>
        </div>
      </div>

      {data ? (
        <div className="flex flex-wrap items-center gap-2">
          {data.department_tabs.map((tab) => (
            <button
              key={tab.department_id}
              type="button"
              className={cn(
                "h-9 rounded-full border px-4 text-[13px] font-medium transition-colors",
                tab.is_selected
                  ? "border-[#dbeafe] bg-white text-[#111827] shadow-[0_1px_2px_rgba(15,23,42,0.06)]"
                  : "border-transparent bg-transparent text-[#6b7280] hover:bg-white/80",
              )}
              onClick={() => selectDepartment(tab.department_id)}
            >
              {tab.tab_label}
            </button>
          ))}
          {data.more_departments.length ? (
            <div className="relative">
              <button
                type="button"
                className="h-9 rounded-full border border-[#dce3ec] bg-white px-4 text-[13px] font-medium text-[#374151]"
                onClick={() => setMoreOpen((v) => !v)}
              >
                More…
              </button>
              {moreOpen ? (
                <ul className="absolute left-0 top-10 z-10 min-w-[8rem] rounded-lg border border-[#e8ecf2] bg-white py-1 shadow-lg">
                  {data.more_departments.map((tab) => (
                    <li key={tab.department_id}>
                      <button
                        type="button"
                        className="block w-full px-4 py-2 text-left text-[13px] text-[#374151] hover:bg-[#f9fafb]"
                        onClick={() => selectDepartment(tab.department_id)}
                      >
                        {tab.tab_label}
                      </button>
                    </li>
                  ))}
                </ul>
              ) : null}
            </div>
          ) : null}
        </div>
      ) : null}

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()} isEmpty={false}>
        {data ? (
          <div className={cn("grid gap-5 xl:grid-cols-[minmax(0,1fr)_18.5rem]", isFetching && "opacity-70")}>
            <div className="space-y-5">
              <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                  <h3 className="text-[14px] font-semibold text-[#111827]">{data.programmes_section_title}</h3>
                </div>
                {data.programmes.length ? (
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[40rem] text-left text-[13px]">
                      <thead>
                        <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                          {progHeaders.map((h, i) => (
                            <th key={h} className={cn("pb-3 font-medium", i === 0 ? "px-5" : "pr-3", i === progHeaders.length - 1 ? "pr-5" : "")}>
                              {h}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#f1f5f9]">
                        {data.programmes.map((row) => (
                          <tr key={row.programme_id} className="hover:bg-[#f9fafb]">
                            <td className="px-5 py-3 font-medium text-[#111827]">{row.programme_name}</td>
                            <td className="py-3 pr-3 text-[#374151]">{row.level_label}</td>
                            <td className="py-3 pr-3 text-[#374151]">{row.duration_label}</td>
                            <td className="py-3 pr-3 tabular-nums text-[#374151]">{row.intake_label}</td>
                            <td className="py-3 pr-3 text-[#374151]">{row.regulation_label}</td>
                            <td className="py-3 pr-5">
                              <StatusPill label={row.status_label} tone={row.status_tone} />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="px-5 py-8 text-sm text-[#9ca3af]">No programmes mapped to this department yet.</p>
                )}
                <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
                  <span>{data.programmes_count_label}</span>
                  <Link href={data.academic_configuration_href} className="font-medium text-[#245dd8] hover:underline">
                    {data.academic_configuration_label}
                  </Link>
                </div>
              </section>

              <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                  <h3 className="text-[14px] font-semibold text-[#111827]">{data.service_courses_section_title}</h3>
                </div>
                {data.service_courses.length ? (
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[36rem] text-left text-[13px]">
                      <thead>
                        <tr className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                          {serviceHeaders.map((h, i) => (
                            <th key={h} className={cn("pb-3 font-medium", i === 0 ? "px-5" : "pr-3", i === serviceHeaders.length - 1 ? "pr-5" : "")}>
                              {h}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#f1f5f9]">
                        {data.service_courses.map((row) => (
                          <tr key={row.course_id} className="hover:bg-[#f9fafb]">
                            <td className="px-5 py-3 font-medium text-[#111827]">{row.course_label}</td>
                            <td className="py-3 pr-3 text-[#374151]">{row.taught_to_label}</td>
                            <td className="py-3 pr-3 tabular-nums text-[#374151]">{row.semester_label}</td>
                            <td className="py-3 pr-5 tabular-nums text-[#374151]">
                              {row.student_count.toLocaleString("en-IN")}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="px-5 py-8 text-sm text-[#9ca3af]">No service courses recorded for this department.</p>
                )}
                <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#f1f5f9] px-5 py-3 text-[12px] text-[#6b7280]">
                  <span>{data.service_courses_count_label}</span>
                  <Link href={data.service_view_all_href} className="font-medium text-[#245dd8] hover:underline">
                    {data.service_view_all_label}
                  </Link>
                </div>
              </section>
            </div>

            <aside className="space-y-4">
              <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.unmapped_section_title}</h3>
                <ul className="mt-3 space-y-3">
                  {data.unmapped_items.length ? (
                    data.unmapped_items.map((item) => (
                      <li key={item.course_id} className="flex items-start justify-between gap-3 border-b border-[#f1f5f9] pb-3 last:border-0 last:pb-0">
                        <div className="min-w-0">
                          <p className="text-[13px] font-medium text-[#111827]">{item.course_label}</p>
                          <p className="mt-0.5 text-[12px] text-[#6b7280]">{item.detail}</p>
                        </div>
                        <ActionPill label={item.action_label} tone={item.action_tone} />
                      </li>
                    ))
                  ) : (
                    <li className="text-[13px] text-[#9ca3af]">All catalogued courses are mapped.</li>
                  )}
                </ul>
              </section>

              <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.course_load_section_title}</h3>
                <ul className="mt-4 space-y-3">
                  {data.course_load_bars.map((bar) => (
                    <li key={bar.key}>
                      <div className="flex items-center justify-between text-[12px] text-[#6b7280]">
                        <span>{bar.label}</span>
                        <span className="tabular-nums font-semibold text-[#111827]">{bar.value}</span>
                      </div>
                      <div className="mt-1.5 h-2 overflow-hidden rounded-full bg-[#e5e7eb]">
                        <div
                          className="h-full rounded-full bg-[#245dd8]"
                          style={{ width: `${bar.max_value ? (bar.value / bar.max_value) * 100 : 0}%` }}
                        />
                      </div>
                    </li>
                  ))}
                </ul>
              </section>
            </aside>
          </div>
        ) : null}
      </QueryState>

      {data ? (
        <footer className="flex flex-col gap-2 border-t border-[#e8ecf2] pt-4 text-[11px] text-[#9ca3af] sm:flex-row sm:items-center sm:justify-between">
          <p>{data.footer_disclaimer}</p>
          <p className="tabular-nums">
            {data.footer_snapshot_label} · {formatSnapshot(data.generated_at)}
          </p>
        </footer>
      ) : null}
    </div>
  );
}