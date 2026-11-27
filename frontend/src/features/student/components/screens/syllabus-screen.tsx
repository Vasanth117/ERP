"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import type { Route } from "next";

import { ArrowDownToLineIcon } from "@/components/icons/erp/generated/arrow-down-to-line";
import { ChevronRightIcon } from "@/components/icons/erp/generated/chevron-right";
import { FileTextIcon } from "@/components/icons/erp/generated/file-text";
import { VideoIcon } from "@/components/icons/erp/generated/video";
import {
  StAcademicsDetailField,
  StAcademicsOutcomeBadge,
  StAcademicsPageBlock,
  StAcademicsSectionCard,
  displayOrDash,
} from "@/features/student/components/ui/student-academics-figma-ui";
import {
  PORTAL_PAGE_DESC,
  STUDENT_BTN_OUTLINE,
  STUDENT_BTN_PRIMARY,
  STUDENT_TAB_PAGE_TITLE,
} from "@/features/student/components/ui/student-portal-tokens";
import { QueryState } from "@/features/student/components/ui/student-screen-ui";
import {
  useCurriculumSubjectList,
  useCurriculumSyllabusPage,
} from "@/features/student/hooks/use-student-curriculum";
import type { CurriculumSyllabusPage, CurriculumSyllabusUnitDetail } from "@/features/student/types/curriculum";
import { cn } from "@/lib/utils";

function formatTopicHours(hours: number): string {
  if (hours <= 0) return "—";
  const label = hours % 1 === 0 ? String(hours) : hours.toFixed(1);
  return `${label} hour${hours === 1 ? "" : "s"}`;
}

export function SyllabusScreen() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const unitAnchorRef = useRef<HTMLDivElement>(null);

  const initialCourse = searchParams.get("course")?.trim() || null;
  const initialUnitRaw = searchParams.get("unit");
  const initialUnit = initialUnitRaw != null && initialUnitRaw !== "" ? Number(initialUnitRaw) : null;

  const [courseCode, setCourseCode] = useState<string | null>(initialCourse);
  const [unitNo, setUnitNo] = useState<number | null>(
    initialUnit != null && !Number.isNaN(initialUnit) ? initialUnit : null,
  );

  const subjectList = useCurriculumSubjectList();
  const syllabusQuery = useCurriculumSyllabusPage(courseCode, unitNo);

  const syncQuery = useCallback(
    (code: string | null, unit: number | null) => {
      const params = new URLSearchParams();
      if (code) params.set("course", code);
      if (unit != null) params.set("unit", String(unit));
      const qs = params.toString();
      router.replace(`${pathname}${qs ? `?${qs}` : ""}` as Route);
    },
    [pathname, router],
  );

  useEffect(() => {
    if (courseCode || subjectList.isLoading || !subjectList.data?.subjects.length) return;
    const first = subjectList.data.subjects[0]!.course_code;
    setCourseCode(first);
    syncQuery(first, initialUnit);
  }, [subjectList.data, subjectList.isLoading, courseCode, initialUnit, syncQuery]);

  useEffect(() => {
    if (unitNo != null || !syllabusQuery.data?.selected_unit_no) return;
    setUnitNo(syllabusQuery.data.selected_unit_no);
  }, [syllabusQuery.data, unitNo]);

  const pickCourse = useCallback(
    (code: string) => {
      setCourseCode(code);
      setUnitNo(null);
      syncQuery(code, null);
    },
    [syncQuery],
  );

  const pickUnit = useCallback(
    (no: number) => {
      setUnitNo(no);
      syncQuery(courseCode, no);
      requestAnimationFrame(() => {
        unitAnchorRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    },
    [courseCode, syncQuery],
  );

  const handleDownload = useCallback(() => {
    if (!syllabusQuery.data) return;
    const blob = new Blob([JSON.stringify(syllabusQuery.data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `syllabus-${syllabusQuery.data.course_code}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [syllabusQuery.data]);

  const courseOptions = useMemo(
    () => subjectList.data?.subjects ?? [],
    [subjectList.data?.subjects],
  );

  const subjectHeadline =
    syllabusQuery.data?.headline ??
    (courseCode && courseOptions.length
      ? courseOptions.find((r) => r.course_code === courseCode)?.course_name
        ? `${courseCode} · ${courseOptions.find((r) => r.course_code === courseCode)!.course_name}`
        : courseCode
      : null);

  const syllabusPending =
    Boolean(courseCode) && (syllabusQuery.isLoading || (syllabusQuery.isFetching && !syllabusQuery.data));

  return (
    <div className="space-y-6">
      <StAcademicsPageBlock
        title="Subject Syllabus"
        description={subjectHeadline ?? "Choose a subject from your programme catalogue"}
        figmaNode="164:8701"
        actions={
          <button
            type="button"
            onClick={handleDownload}
            disabled={!syllabusQuery.data}
            className={cn(STUDENT_BTN_PRIMARY, !syllabusQuery.data && "pointer-events-none opacity-50")}
          >
            <ArrowDownToLineIcon className="size-3.5 stroke-[2]" aria-hidden />
            <span>Download PDF</span>
          </button>
        }
      >
        <QueryState
          isLoading={subjectList.isLoading}
          isError={subjectList.isError}
          error={subjectList.error}
          onRetry={() => void subjectList.refetch()}
          isEmpty={!subjectList.isLoading && courseOptions.length === 0}
          emptyMessage="No subjects in your programme catalogue yet. Ask college admin to publish the programme curriculum."
        >
          <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
            <label className="flex min-w-[14rem] flex-1 flex-col gap-1 text-[11px] text-[#6b7280]">
              Subject
              <select
                aria-label="Subject"
                value={courseCode ?? ""}
                onChange={(e) => pickCourse(e.target.value)}
                disabled={courseOptions.length === 0}
                className="h-9 rounded-md border border-[#dce3ec] bg-white px-3 text-[13px] text-[#111827] disabled:opacity-60"
              >
                <option value="" disabled>
                  {subjectList.isLoading ? "Loading subjects…" : "Select subject"}
                </option>
                {courseOptions.map((row) => (
                  <option key={row.course_id} value={row.course_code}>
                    {row.course_code} · {row.course_name}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </QueryState>

        <QueryState
          isLoading={syllabusPending}
          isError={syllabusQuery.isError}
          error={syllabusQuery.error}
          onRetry={() => void syllabusQuery.refetch()}
          isEmpty={!courseCode && !subjectList.isLoading && courseOptions.length > 0}
          emptyMessage="Select a subject to view the syllabus."
        >
          {syllabusQuery.data ? (
            <StAcademicsSectionCard
              title={syllabusQuery.data.units_panel_title}
              footer={<span>{syllabusQuery.data.units_footer_label}</span>}
            >
              {syllabusQuery.data.units.length === 0 ? (
                <p className="px-5 py-10 text-center text-[13px] text-[#607086]">
                  No units published for this syllabus yet.
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[640px] text-left text-[13px]">
                    <thead>
                      <tr className="border-b border-[#e8ecf2] text-[11px] font-medium uppercase tracking-wide text-[#6b7280]">
                        {syllabusQuery.data.table_headers.map((header) => (
                          <th key={header} className="px-5 py-3">
                            {header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#e8ecf2]">
                      {syllabusQuery.data.units.map((row) => {
                        const selected =
                          (unitNo ?? syllabusQuery.data!.selected_unit_no) === row.unit_no;
                        return (
                          <tr
                            key={row.unit_no}
                            className={cn(
                              "cursor-pointer text-[#172b45] transition-colors",
                              selected ? "bg-[#f0f6ff]" : "hover:bg-[#f9fafb]",
                            )}
                            onClick={() => pickUnit(row.unit_no)}
                          >
                            <td className="px-5 py-3.5 tabular-nums font-medium">{row.unit_no}</td>
                            <td className="px-5 py-3.5 font-medium">{row.title}</td>
                            <td className="px-5 py-3.5 tabular-nums">{row.planned_hours}</td>
                            <td className="px-5 py-3.5 tabular-nums">{row.topic_count}</td>
                            <td className="px-5 py-3.5">
                              <StAcademicsOutcomeBadge label={row.progress_label} tone={row.progress_tone} />
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </StAcademicsSectionCard>
          ) : null}
        </QueryState>
      </StAcademicsPageBlock>

      <div ref={unitAnchorRef}>
        <QueryState
          isLoading={syllabusQuery.isLoading && Boolean(courseCode)}
          isError={syllabusQuery.isError}
          error={syllabusQuery.error}
          onRetry={() => void syllabusQuery.refetch()}
        >
          {syllabusQuery.data?.unit_detail ? (
            <UnitSyllabusPanel
              page={syllabusQuery.data}
              detail={syllabusQuery.data.unit_detail}
              onBack={() => {
                if (!syllabusQuery.data?.units.length) return;
                pickUnit(syllabusQuery.data.units[0]!.unit_no);
              }}
            />
          ) : courseCode ? (
            <StAcademicsSectionCard title="Unit-wise syllabus details">
              <p className="px-5 py-10 text-center text-[13px] text-[#607086]">
                {syllabusQuery.data?.units.length
                  ? "Select a unit in the table above to view topics and resources."
                  : "Syllabus units are not available for this subject yet."}
              </p>
            </StAcademicsSectionCard>
          ) : null}
        </QueryState>
      </div>
    </div>
  );
}

function UnitSyllabusPanel({
  page,
  detail,
  onBack,
}: {
  page: CurriculumSyllabusPage;
  detail: CurriculumSyllabusUnitDetail;
  onBack: () => void;
}) {
  const openMaterials = detail.open_materials_url ? (
    <Link
      href={detail.open_materials_url as Route}
      target="_blank"
      rel="noopener noreferrer"
      className={cn(STUDENT_BTN_PRIMARY, "gap-1.5")}
    >
      <VideoIcon className="size-3.5 stroke-[2]" aria-hidden />
      <span>Open materials</span>
    </Link>
  ) : (
    <button type="button" disabled className={cn(STUDENT_BTN_PRIMARY, "gap-1.5 opacity-50")}>
      <VideoIcon className="size-3.5 stroke-[2]" aria-hidden />
      <span>Open materials</span>
    </button>
  );

  return (
    <section className="space-y-5" data-figma-frame="164:9036">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex min-w-0 items-start gap-2">
          <button
            type="button"
            onClick={onBack}
            className={cn(STUDENT_BTN_OUTLINE, "size-9 shrink-0 p-0")}
            aria-label="First unit"
          >
            <ChevronRightIcon className="size-4 rotate-180 stroke-[2]" aria-hidden />
          </button>
          <div>
            <h2 className={STUDENT_TAB_PAGE_TITLE}>{detail.page_title}</h2>
            <p className={PORTAL_PAGE_DESC}>{detail.headline}</p>
            <p className="mt-0.5 text-[12px] text-[#6b7280]">{page.headline}</p>
          </div>
        </div>
        {openMaterials}
      </header>

      <div className="grid items-start gap-5 lg:grid-cols-12">
        <div className="lg:col-span-8">
          <StAcademicsSectionCard title="Topics">
            {detail.topics.length === 0 ? (
              <p className="px-5 py-8 text-[13px] text-[#607086]">No topics listed for this unit.</p>
            ) : (
              <ul className="divide-y divide-[#e8ecf2]">
                {detail.topics.map((topic) => (
                  <li key={topic.title} className="flex items-start gap-3 px-5 py-3.5">
                    <FileTextIcon className="mt-0.5 size-4 shrink-0 text-[#6b7280]" aria-hidden />
                    <div className="min-w-0 flex-1">
                      <p className="text-[13px] font-semibold text-[#172b45]">{topic.title}</p>
                      <p className="text-[12px] text-[#6b7280]">{formatTopicHours(topic.hours)}</p>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </StAcademicsSectionCard>
        </div>

        <div className="space-y-5 lg:col-span-4">
          <StAcademicsSectionCard title="Unit">
            <div className="space-y-3 px-5 py-2">
              <StAcademicsDetailField
                label="Hours"
                value={displayOrDash(
                  detail.planned_hours % 1 === 0
                    ? detail.planned_hours
                    : detail.planned_hours.toFixed(1),
                )}
              />
              <StAcademicsDetailField
                label="Weightage"
                value={
                  detail.weightage_pct != null ? `${detail.weightage_pct}%` : "—"
                }
              />
              <StAcademicsDetailField
                label="CO mapping"
                value={detail.co_mapping_label ?? "—"}
              />
            </div>
          </StAcademicsSectionCard>

          <StAcademicsSectionCard title="Learning resources">
            {detail.learning_resources.length === 0 ? (
              <p className="px-5 py-8 text-[13px] text-[#607086]">
                No published materials for this unit yet.
              </p>
            ) : (
              <ul className="divide-y divide-[#e8ecf2]">
                {detail.learning_resources.map((resource) => (
                  <li key={`${resource.title}-${resource.subtitle ?? ""}`} className="px-5 py-3.5">
                    {resource.url ? (
                      <Link
                        href={resource.url as Route}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="group flex items-start gap-3"
                      >
                        <FileTextIcon className="mt-0.5 size-4 shrink-0 text-[#6b7280]" aria-hidden />
                        <div>
                          <p className="text-[13px] font-semibold text-[#172b45] group-hover:text-[#1d4ed8]">
                            {resource.title}
                          </p>
                          {resource.subtitle ? (
                            <p className="text-[12px] text-[#6b7280]">{resource.subtitle}</p>
                          ) : null}
                        </div>
                      </Link>
                    ) : (
                      <div className="flex items-start gap-3">
                        <FileTextIcon className="mt-0.5 size-4 shrink-0 text-[#6b7280]" aria-hidden />
                        <div>
                          <p className="text-[13px] font-semibold text-[#172b45]">{resource.title}</p>
                          {resource.subtitle ? (
                            <p className="text-[12px] text-[#6b7280]">{resource.subtitle}</p>
                          ) : null}
                        </div>
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </StAcademicsSectionCard>
        </div>
      </div>
    </section>
  );
}