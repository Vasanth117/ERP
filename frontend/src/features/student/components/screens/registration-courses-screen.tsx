"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";

import { ChevronLeftIcon } from "@/components/icons/erp/generated/chevron-left";
import { ChevronRightIcon } from "@/components/icons/erp/generated/chevron-right";
import { PlusIcon } from "@/components/icons/erp/generated/plus";
import { CollegeAdminIcon } from "@/features/college-admin/components/layout/college-admin-icon";
import {
  StAcademicsDetailRow,
  StAcademicsOutcomeBadge,
  StAcademicsPageBlock,
  StAcademicsSectionCard,
} from "@/features/student/components/ui/student-academics-figma-ui";
import { QueryState } from "@/features/student/components/ui/student-screen-ui";
import {
  PORTAL_SURFACE_BORDER,
  STUDENT_BTN_OUTLINE,
  STUDENT_BTN_PRIMARY,
} from "@/features/student/components/ui/student-portal-tokens";
import {
  useRegistrationCourseDetailPage,
  useRegistrationCoursesPage,
} from "@/features/student/hooks/use-student-registration";
import type { RegistrationCourseDetailPage, RegistrationCoursesPage } from "@/features/student/types/registration";
import { cn } from "@/lib/utils";

export function RegistrationCoursesScreen() {
  const searchParams = useSearchParams();
  const initialCourse = searchParams.get("course")?.trim() || null;
  const detailsRef = useRef<HTMLDivElement>(null);

  const [category, setCategory] = useState("all");
  const [search, setSearch] = useState("");
  const [selectedCode, setSelectedCode] = useState<string | null>(initialCourse);
  const [semester, setSemester] = useState<string | undefined>(undefined);

  const listParams = useMemo(
    () => ({
      semester,
      category: category === "all" ? undefined : category,
      q: search.trim() || undefined,
    }),
    [semester, category, search],
  );

  const listQuery = useRegistrationCoursesPage(listParams);
  const detailQuery = useRegistrationCourseDetailPage(selectedCode);

  useEffect(() => {
    if (selectedCode || !listQuery.data?.default_course_code) return;
    setSelectedCode(listQuery.data.default_course_code);
  }, [listQuery.data, selectedCode]);

  const pickCourse = useCallback((code: string) => {
    setSelectedCode(code);
    requestAnimationFrame(() => {
      detailsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }, []);

  return (
    <div className="flex flex-col gap-4">
      <StAcademicsPageBlock
        title={listQuery.data?.page_title ?? "Available Courses"}
        description={listQuery.data?.page_subtitle ?? "Courses you are eligible for"}
        figmaNode="164:10975"
        actions={
          <Link href={listQuery.data?.go_to_selection_href ?? "/student/registration/submit"} className={STUDENT_BTN_PRIMARY}>
            <ChevronRightIcon className="size-3.5 stroke-[2]" aria-hidden />
            <span>Go to selection</span>
          </Link>
        }
      >
        <QueryState
          isLoading={listQuery.isLoading}
          isError={listQuery.isError}
          error={listQuery.error}
          onRetry={() => void listQuery.refetch()}
        >
          {listQuery.data ? (
            <RegistrationCoursesList
              data={listQuery.data}
              category={category}
              setCategory={setCategory}
              search={search}
              setSearch={setSearch}
              semester={semester ?? listQuery.data.selected_semester}
              setSemester={setSemester}
              selectedCode={selectedCode}
              onPickCourse={pickCourse}
            />
          ) : null}
        </QueryState>
      </StAcademicsPageBlock>

      <section ref={detailsRef} id="st-04-03-course-details" className="scroll-mt-4 border-t border-[#e8ecf2] pt-3">
        <QueryState
          isLoading={detailQuery.isLoading && Boolean(selectedCode)}
          isError={detailQuery.isError}
          error={detailQuery.error}
          onRetry={() => void detailQuery.refetch()}
        >
          {detailQuery.data ? (
            <RegistrationCourseDetailBlock data={detailQuery.data} />
          ) : selectedCode ? null : (
            <p className="text-[13px] text-[#6b7280]">Select a course from the table above.</p>
          )}
        </QueryState>
      </section>
    </div>
  );
}

function RegistrationCoursesList({
  data,
  category,
  setCategory,
  search,
  setSearch,
  semester,
  setSemester,
  selectedCode,
  onPickCourse,
}: {
  data: RegistrationCoursesPage;
  category: string;
  setCategory: (v: string) => void;
  search: string;
  setSearch: (v: string) => void;
  semester: string;
  setSemester: (v: string) => void;
  selectedCode: string | null;
  onPickCourse: (code: string) => void;
}) {
  return (
    <div className="space-y-3">
      <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center">
        <div className="relative min-w-[200px] flex-1">
          <CollegeAdminIcon
            name="search"
            size={16}
            className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[#9ca3af]"
          />
          <input
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={data.search_placeholder}
            className={cn(
              "h-9 w-full rounded border bg-white pl-9 pr-3 text-[13px] text-[#111827] outline-none focus:border-[#245dd8]",
              PORTAL_SURFACE_BORDER,
            )}
          />
        </div>
        <label className="sr-only" htmlFor="reg-semester-filter">
          Semester
        </label>
        <select
          id="reg-semester-filter"
          value={semester}
          onChange={(e) => setSemester(e.target.value)}
          className={cn("h-9 rounded border bg-white px-3 text-[13px]", PORTAL_SURFACE_BORDER)}
        >
          {data.semester_options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        <label className="sr-only" htmlFor="reg-category-filter">
          Category
        </label>
        <select
          id="reg-category-filter"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className={cn("h-9 rounded border bg-white px-3 text-[13px]", PORTAL_SURFACE_BORDER)}
        >
          {data.category_options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      <StAcademicsSectionCard title="Available courses" footer={<span>{data.courses_footer_label}</span>}>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px] text-left text-[13px]">
            <thead>
              <tr className="border-b border-[#e8ecf2] text-[11px] font-medium uppercase tracking-wide text-[#6b7280]">
                <th className="px-4 py-2.5 font-medium">Code</th>
                <th className="px-4 py-2.5 font-medium">Course</th>
                <th className="px-4 py-2.5 font-medium">Category</th>
                <th className="px-4 py-2.5 font-medium">Credits</th>
                <th className="px-4 py-2.5 font-medium">Prerequisite</th>
                <th className="px-4 py-2.5 font-medium">Seats</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#e8ecf2]">
              {data.courses.map((row) => {
                const selected = selectedCode === row.course_code;
                return (
                  <tr key={row.course_id} className={cn("text-[#172b45]", selected && "bg-[#f8fafc]")}>
                    <td className="px-4 py-2.5">
                      <button
                        type="button"
                        onClick={() => onPickCourse(row.course_code)}
                        className="font-semibold tabular-nums text-[#245dd8] hover:underline"
                      >
                        {row.course_code}
                      </button>
                    </td>
                    <td className="px-4 py-2.5">{row.course_name}</td>
                    <td className="px-4 py-2.5 text-[#6b7280]">{row.category_label}</td>
                    <td className="px-4 py-2.5 tabular-nums">{row.credit_units}</td>
                    <td className="px-4 py-2.5 text-[#6b7280]">{row.prerequisite_label}</td>
                    <td className="px-4 py-2.5 text-[#6b7280]">{row.seats_label}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </StAcademicsSectionCard>
    </div>
  );
}

function RegistrationCourseDetailBlock({ data }: { data: RegistrationCourseDetailPage }) {
  return (
    <StAcademicsPageBlock
      title={data.page_title}
      description={data.headline}
      figmaNode="164:11309"
      compact
      belowDescription={
        <Link
          href={data.back_href}
          className="inline-flex items-center gap-1 text-[12px] font-medium text-[#6b7280] hover:text-[#245dd8]"
        >
          <ChevronLeftIcon className="size-3.5 stroke-[2]" aria-hidden />
          Back to courses
        </Link>
      }
      actions={
        data.show_add_to_selection ? (
          <Link href={data.add_to_selection_href} className={STUDENT_BTN_PRIMARY}>
            <PlusIcon className="size-3.5 stroke-[2]" aria-hidden />
            <span>Add to selection</span>
          </Link>
        ) : null
      }
    >
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_280px]">
        <div className="space-y-4">
          <StAcademicsSectionCard title="Course">
            <div className="px-5 py-3">
              <StAcademicsDetailRow
                fields={[
                  { label: "Code", value: data.course_code },
                  { label: "Category", value: data.category_label },
                  { label: "Credits", value: String(data.credit_units) },
                  { label: "Faculty", value: data.faculty_label },
                  { label: "Seats", value: data.seats_label },
                  { label: "Slot", value: data.slot_label },
                ]}
              />
            </div>
          </StAcademicsSectionCard>

          <StAcademicsSectionCard title="Description">
            <p className="px-5 py-3 text-[13px] leading-snug text-[#374151]">{data.description}</p>
          </StAcademicsSectionCard>
        </div>

        <StAcademicsSectionCard title="Eligibility">
          <ul className="divide-y divide-[#e8ecf2]">
            {data.eligibility.map((item) => (
              <li key={item.key} className="flex items-start justify-between gap-3 px-4 py-3">
                <div className="min-w-0">
                  <p className="text-[13px] font-medium text-[#111827]">{item.title}</p>
                  <p className="mt-0.5 text-[12px] text-[#6b7280]">{item.detail}</p>
                </div>
                <StAcademicsOutcomeBadge label={item.status_label} tone={item.status_tone} />
              </li>
            ))}
          </ul>
        </StAcademicsSectionCard>
      </div>
    </StAcademicsPageBlock>
  );
}