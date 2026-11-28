"use client";

import { CollegeAdminModulePageLayout } from "@/features/college-admin/components/layout/college-admin-module-page-layout";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { BuildingIcon } from "@/components/icons/erp/generated/building";
import { LayersIcon } from "@/components/icons/erp/generated/layers";
import { downloadLmsUnitsChaptersExport } from "@/features/college-admin/api/lms-content";
import { LmsContentPageHeaderActions } from "@/features/college-admin/components/lms/lms-content-page-header-actions";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useLmsUnitChapterManagementPage } from "@/features/college-admin/hooks/use-lms-content";
import type { LmsUnitChapterManagementPage } from "@/features/college-admin/types/lms-content";
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

function mergeView(data: LmsUnitChapterManagementPage | undefined) {
  return {
    page_title: data?.page_title ?? "Unit & Chapter Management",
    page_subtitle: data?.page_subtitle ?? "Course structure",
    export_label: data?.export_label ?? "Export",
    primary_action_label: data?.primary_action_label ?? "Add unit",
    primary_action_href: data?.primary_action_href ?? "#",
    course_header_label: data?.course_header_label ?? "—",
    course_options: data?.course_options ?? [],
    unit_rows: data?.unit_rows ?? [],
    empty_message: data?.empty_message ?? "",
  };
}

export function LmsUnitChapterManagementDashboard() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const courseFromUrl = searchParams.get("course_code") ?? undefined;
  const queryParams = useMemo(() => ({ course_code: courseFromUrl }), [courseFromUrl]);
  const { data, isLoading, isError, error, refetch, isFetching } = useLmsUnitChapterManagementPage(queryParams);
  const view = mergeView(data);

  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  useEffect(() => {
    setExpanded({});
  }, [courseFromUrl]);

  const selectedCourse = view.course_options.find((o) => o.selected)?.course_code ?? "";

  const handleExport = useCallback(() => {
    void downloadLmsUnitsChaptersExport(
      selectedCourse ? { course_code: selectedCourse } : undefined,
    ).catch(() => undefined);
  }, [selectedCourse]);

  return (
    <CollegeAdminModulePageLayout figmaFrame="161:12622">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">{view.page_title}</h2>
          {view.page_subtitle ? <p className="mt-1 text-[14px] text-[#6b7280]">{view.page_subtitle}</p> : null}
        </div>
        <LmsContentPageHeaderActions
          exportLabel={view.export_label}
          exportDisabled={isLoading || isFetching}
          onExport={handleExport}
          primaryHref={view.primary_action_href}
          primaryLabel={view.primary_action_label}
          primaryMode="plus"
        />
      </div>

      {view.course_options.length > 1 ? (
        <div className="flex flex-wrap items-center gap-2">
          <label htmlFor="lms-unit-course" className="text-[13px] text-[#6b7280]">
            Course
          </label>
          <select
            id="lms-unit-course"
            value={selectedCourse}
            onChange={(e) => {
              const code = e.target.value;
              const params = new URLSearchParams(searchParams.toString());
              if (code) params.set("course_code", code);
              else params.delete("course_code");
              const qs = params.toString();
              router.push(qs ? `${pathname}?${qs}` : pathname);
            }}
            className="h-9 min-w-[14rem] max-w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px] text-[#374151]"
          >
            {view.course_options.map((opt) => (
              <option key={opt.course_code} value={opt.course_code}>
                {opt.course_label}
              </option>
            ))}
          </select>
        </div>
      ) : null}

      {isLoading || isFetching ? (
        <p className="text-[12px] text-[#9ca3af]">{isLoading ? "Loading course structure…" : "Updating…"}</p>
      ) : null}

      {isError ? (
        <QueryState isError={isError} error={error} onRetry={() => void refetch()}>
          <></>
        </QueryState>
      ) : !data ? null : (
        <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
          <div className="border-b border-[#f1f5f9] px-5 py-3.5">
            <h3 className="text-[14px] font-semibold text-[#111827]">{view.course_header_label}</h3>
          </div>

          {view.unit_rows.length ? (
            <ul className="divide-y divide-[#f1f5f9]">
              {view.unit_rows.map((unit) => {
                const isOpen = expanded[unit.row_key] ?? unit.default_expanded;
                return (
                  <li key={unit.row_key}>
                    <button
                      type="button"
                      className="flex w-full items-center gap-3 px-5 py-3.5 text-left hover:bg-[#f9fafb]"
                      onClick={() =>
                        setExpanded((prev) => ({ ...prev, [unit.row_key]: !isOpen }))
                      }
                      aria-expanded={isOpen}
                    >
                      <span className="inline-flex size-9 shrink-0 items-center justify-center rounded-lg bg-[#eff6ff] text-[#245dd8]">
                        <BuildingIcon className="size-4" aria-hidden />
                      </span>
                      <span className="min-w-0 flex-1">
                        <span className="block text-[14px] font-semibold text-[#111827]">{unit.unit_label}</span>
                        <span className="mt-0.5 block text-[12px] text-[#9ca3af]">{unit.chapter_count_label}</span>
                      </span>
                      <StatusPill label={unit.status_label} tone={unit.status_tone} />
                    </button>

                    {isOpen && unit.chapters.length ? (
                      <ul className="border-t border-[#f8fafc] bg-[#fafbfc] pb-1">
                        {unit.chapters.map((chapter) => (
                          <li key={chapter.row_key}>
                            {chapter.detail_href ? (
                              <Link
                                href={chapter.detail_href}
                                className="flex items-center gap-3 py-2.5 pl-[4.25rem] pr-5 hover:bg-[#f3f4f6]"
                              >
                                <LayersIcon className="size-4 shrink-0 text-[#9ca3af]" aria-hidden />
                                <span className="min-w-0 flex-1">
                                  <span className="block text-[13px] font-medium text-[#374151]">
                                    {chapter.chapter_label}
                                  </span>
                                  <span className="mt-0.5 block text-[12px] text-[#9ca3af]">
                                    {chapter.materials_count_label}
                                  </span>
                                </span>
                              </Link>
                            ) : (
                              <div className="flex items-center gap-3 py-2.5 pl-[4.25rem] pr-5">
                                <LayersIcon className="size-4 shrink-0 text-[#9ca3af]" aria-hidden />
                                <span className="min-w-0 flex-1">
                                  <span className="block text-[13px] font-medium text-[#374151]">
                                    {chapter.chapter_label}
                                  </span>
                                  <span className="mt-0.5 block text-[#9ca3af] text-[12px]">
                                    {chapter.materials_count_label}
                                  </span>
                                </span>
                              </div>
                            )}
                          </li>
                        ))}
                      </ul>
                    ) : null}
                  </li>
                );
              })}
            </ul>
          ) : (
            <p className="px-5 py-10 text-center text-sm text-[#9ca3af]">{view.empty_message}</p>
          )}
        </section>
      )}
    </CollegeAdminModulePageLayout>
  );
}