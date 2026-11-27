"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import type { Route } from "next";

import { CheckIcon } from "@/components/icons/erp/generated/check";
import { ChevronRightIcon } from "@/components/icons/erp/generated/chevron-right";
import { ArrowDownToLineIcon } from "@/components/icons/erp/generated/arrow-down-to-line";
import { CollegeAdminIcon } from "@/features/college-admin/components/layout/college-admin-icon";
import {
  StAcademicsDetailRow,
  StAcademicsOutcomeBadge,
  StAcademicsPageBlock,
  StAcademicsSectionCard,
  displayOrDash,
} from "@/features/student/components/ui/student-academics-figma-ui";
import {
  PORTAL_PAGE_DESC,
  PORTAL_SURFACE_BORDER,
  STUDENT_BTN_OUTLINE,
  STUDENT_BTN_PRIMARY,
  STUDENT_TAB_PAGE_TITLE,
} from "@/features/student/components/ui/student-portal-tokens";
import { QueryState } from "@/features/student/components/ui/student-screen-ui";
import {
  useCurriculumSubjectDetail,
  useCurriculumSubjectList,
} from "@/features/student/hooks/use-student-curriculum";
import type { CurriculumSubjectDetail } from "@/features/student/types/curriculum";
import type { CurriculumSubjectListParams } from "@/features/student/api/curriculum";
import { cn } from "@/lib/utils";

export function SubjectsScreen() {
  const searchParams = useSearchParams();
  const initialCourse = searchParams.get("course")?.trim() || null;
  const detailsAnchorRef = useRef<HTMLDivElement>(null);

  const [selectedCode, setSelectedCode] = useState<string | null>(initialCourse);
  const [semester, setSemester] = useState<number | "all">("all");
  const [category, setCategory] = useState("all");
  const [status, setStatus] = useState("all");
  const [search, setSearch] = useState("");

  const listParams = useMemo<CurriculumSubjectListParams>(
    () => ({
      semester: semester === "all" ? undefined : semester,
      category,
      status,
      q: search.trim() || undefined,
    }),
    [semester, category, status, search],
  );

  const listQuery = useCurriculumSubjectList(listParams);
  const detailQuery = useCurriculumSubjectDetail(selectedCode);

  useEffect(() => {
    if (selectedCode || !listQuery.data?.subjects.length) return;
    setSelectedCode(listQuery.data.subjects[0]!.course_code);
  }, [listQuery.data, selectedCode]);

  const selectSubject = useCallback((code: string) => {
    setSelectedCode(code);
    requestAnimationFrame(() => {
      detailsAnchorRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }, []);

  const handleDownload = useCallback(() => {
    if (!listQuery.data) return;
    const blob = new Blob([JSON.stringify(listQuery.data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "subject-list.json";
    a.click();
    URL.revokeObjectURL(url);
  }, [listQuery.data]);

  return (
    <div className="space-y-6">
      <StAcademicsPageBlock
        title="Subject list"
        description={listQuery.data?.page_subtitle ?? "Filter by semester, category or completion"}
        figmaNode="164:7994"
        actions={
          <button type="button" onClick={handleDownload} className={STUDENT_BTN_PRIMARY}>
            <ArrowDownToLineIcon className="size-3.5 stroke-[2]" aria-hidden />
            <span>Download</span>
          </button>
        }
      >
        <SubjectListFilters
          semester={semester}
          category={category}
          status={status}
          search={search}
          list={listQuery.data}
          onSemesterChange={setSemester}
          onCategoryChange={setCategory}
          onStatusChange={setStatus}
          onSearchChange={setSearch}
        />

        <QueryState
          isLoading={listQuery.isLoading}
          isError={listQuery.isError}
          error={listQuery.error}
          onRetry={() => void listQuery.refetch()}
        >
          {listQuery.data ? (
            <StAcademicsSectionCard title="Subjects" footer={<span>{listQuery.data.footer_label}</span>}>
              {listQuery.data.subjects.length === 0 ? (
                <p className="px-5 py-10 text-center text-[13px] text-[#607086]">
                  No subjects match your filters.
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[640px] text-left text-[13px]">
                    <thead>
                      <tr className="border-b border-[#e8ecf2] text-[11px] font-medium uppercase tracking-wide text-[#6b7280]">
                        {listQuery.data.table_headers.map((header) => (
                          <th key={header} className="px-5 py-3">
                            {header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#e8ecf2]">
                      {listQuery.data.subjects.map((row) => {
                        const selected = row.course_code === selectedCode;
                        return (
                          <tr
                            key={row.course_id}
                            className={cn(
                              "cursor-pointer text-[#172b45] transition-colors",
                              selected ? "bg-[#f0f6ff]" : "hover:bg-[#f9fafb]",
                            )}
                            onClick={() => selectSubject(row.course_code)}
                          >
                            <td className="px-5 py-3.5 font-mono text-[12px] font-semibold">{row.course_code}</td>
                            <td className="px-5 py-3.5 font-medium">{row.course_name}</td>
                            <td className="px-5 py-3.5">{row.category_label}</td>
                            <td className="px-5 py-3.5 font-mono text-[12px]">{row.ltp_label}</td>
                            <td className="px-5 py-3.5 tabular-nums">{row.credits}</td>
                            <td className="px-5 py-3.5">
                              <StAcademicsOutcomeBadge label={row.status_label} tone={row.status_tone} />
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

      <div ref={detailsAnchorRef} className="space-y-6">
        <QueryState
          isLoading={detailQuery.isLoading && Boolean(selectedCode)}
          isError={detailQuery.isError}
          error={detailQuery.error}
          onRetry={() => void detailQuery.refetch()}
        >
          {selectedCode && detailQuery.data ? (
            <>
              <SubjectDetailsPanel data={detailQuery.data} onClear={() => setSelectedCode(null)} />
              <SubjectCreditDetailsPanel data={detailQuery.data} />
            </>
          ) : (
            <StAcademicsSectionCard title="Subject details">
              <p className="px-5 py-10 text-center text-[13px] text-[#607086]">
                {listQuery.data?.subjects.length
                  ? "Select a subject in the list above to view details."
                  : "No subjects in your programme catalogue yet."}
              </p>
            </StAcademicsSectionCard>
          )}
        </QueryState>
      </div>
    </div>
  );
}

function SubjectListFilters({
  semester,
  category,
  status,
  search,
  list,
  onSemesterChange,
  onCategoryChange,
  onStatusChange,
  onSearchChange,
}: {
  semester: number | "all";
  category: string;
  status: string;
  search: string;
  list: ReturnType<typeof useCurriculumSubjectList>["data"];
  onSemesterChange: (v: number | "all") => void;
  onCategoryChange: (v: string) => void;
  onStatusChange: (v: string) => void;
  onSearchChange: (v: string) => void;
}) {
  return (
    <div className="flex flex-col gap-3 lg:flex-row lg:flex-wrap lg:items-center">
      <input
        type="search"
        placeholder="Search subject or code"
        value={search}
        onChange={(e) => onSearchChange(e.target.value)}
        className="h-9 min-w-[12rem] flex-1 rounded-md border border-[#dce3ec] bg-white px-3 text-[13px] text-[#111827] placeholder:text-[#9ca3af]"
      />
      <select
        aria-label="Semester"
        value={semester === "all" ? "all" : String(semester)}
        onChange={(e) => {
          const v = e.target.value;
          onSemesterChange(v === "all" ? "all" : Number(v));
        }}
        className="h-9 rounded-md border border-[#dce3ec] bg-white px-3 text-[13px]"
      >
        {list?.semester_options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        )) ?? <option value="all">All semesters</option>}
      </select>
      <select
        aria-label="Category"
        value={category}
        onChange={(e) => onCategoryChange(e.target.value)}
        className="h-9 rounded-md border border-[#dce3ec] bg-white px-3 text-[13px]"
      >
        {(list?.category_options ?? []).map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
      <select
        aria-label="Status"
        value={status}
        onChange={(e) => onStatusChange(e.target.value)}
        className="h-9 rounded-md border border-[#dce3ec] bg-white px-3 text-[13px]"
      >
        {(list?.status_options ?? []).map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </div>
  );
}

function SubjectDetailsPanel({
  data,
  onClear,
}: {
  data: CurriculumSubjectDetail;
  onClear: () => void;
}) {
  const subjectFields = [
    { label: "Code", value: data.code },
    { label: "Category", value: data.category_label },
    { label: "Credits", value: displayOrDash(data.credits) },
    { label: "L-T-P", value: data.ltp_label },
    { label: "Faculty", value: data.faculty_label },
    { label: "Regulation", value: data.regulation_label ?? "—" },
  ];

  return (
    <section className="space-y-5" data-figma-frame="164:8360">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex min-w-0 items-start gap-2">
          <button
            type="button"
            onClick={onClear}
            className={cn(STUDENT_BTN_OUTLINE, "size-9 shrink-0 p-0")}
            aria-label="Clear selection"
          >
            ←
          </button>
          <div>
            <h2 className={STUDENT_TAB_PAGE_TITLE}>{data.page_title}</h2>
            <p className={PORTAL_PAGE_DESC}>{data.headline}</p>
          </div>
        </div>
        <Link href={data.syllabus_href as Route} className={cn(STUDENT_BTN_PRIMARY, "gap-1")}>
          <ChevronRightIcon className="size-3.5 stroke-[2]" aria-hidden />
          <span>Syllabus</span>
        </Link>
      </header>

      <div className="grid items-start gap-5 lg:grid-cols-12">
        <div className="space-y-5 lg:col-span-8">
          <StAcademicsSectionCard title="Subject">
            <div className="px-5 py-2">
              <StAcademicsDetailRow fields={subjectFields.slice(0, 2)} />
              <StAcademicsDetailRow fields={subjectFields.slice(2, 4)} />
              <StAcademicsDetailRow fields={subjectFields.slice(4, 6)} />
            </div>
          </StAcademicsSectionCard>

          <StAcademicsSectionCard title="Course objectives">
            {data.objectives.length === 0 ? (
              <p className="px-5 py-8 text-[13px] text-[#607086]">No objectives published yet.</p>
            ) : (
              <ul className="divide-y divide-[#e8ecf2]">
                {data.objectives.map((item) => (
                  <li key={item} className="flex gap-3 px-5 py-3.5 text-[13px] text-[#172b45]">
                    <CheckIcon className="mt-0.5 size-4 shrink-0 text-[#2563eb]" aria-hidden />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            )}
          </StAcademicsSectionCard>
        </div>

        <div className="space-y-5 lg:col-span-4">
          <StAcademicsSectionCard title="Assessment">
            {data.assessments.length === 0 ? (
              <p className="px-5 py-8 text-[13px] text-[#607086]">Assessment split not configured.</p>
            ) : (
              <ul className={cn("divide-y", PORTAL_SURFACE_BORDER)}>
                {data.assessments.map((item) => (
                  <li key={item.label} className="flex items-start gap-3 px-5 py-3.5">
                    <CollegeAdminIcon
                      name={item.kind === "external" ? "calculator" : "file-text"}
                      size={18}
                      className="mt-0.5 text-[#6b7280]"
                    />
                    <div>
                      <p className="text-[13px] font-medium text-[#172b45]">{item.label}</p>
                      <p className="text-[12px] text-[#6b7280]">{item.marks_label}</p>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </StAcademicsSectionCard>

          <StAcademicsSectionCard title="Resources">
            {data.resources.length === 0 ? (
              <p className="px-5 py-8 text-[13px] text-[#607086]">No resources listed.</p>
            ) : (
              <ul className={cn("divide-y", PORTAL_SURFACE_BORDER)}>
                {data.resources.map((item) => (
                  <li key={item.title} className="flex items-start gap-3 px-5 py-3.5">
                    <CollegeAdminIcon
                      name={item.kind === "lms" ? "monitor" : "book-open"}
                      size={18}
                      className="mt-0.5 text-[#6b7280]"
                    />
                    <div>
                      <p className="text-[13px] font-medium text-[#172b45]">{item.title}</p>
                      {item.subtitle ? (
                        <p className="text-[12px] text-[#6b7280]">{item.subtitle}</p>
                      ) : null}
                    </div>
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

function SubjectCreditDetailsPanel({ data }: { data: CurriculumSubjectDetail }) {
  const credit = data.credit_details;

  return (
    <section className="space-y-4" data-figma-frame="ST03.07">
      <header>
        <h2 className={STUDENT_TAB_PAGE_TITLE}>{credit.page_title}</h2>
        <p className={PORTAL_PAGE_DESC}>{credit.page_subtitle}</p>
      </header>

      <StAcademicsSectionCard title={credit.panel_title} footer={<span>{credit.footer_label}</span>}>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[32rem] text-left text-[13px]">
            <thead>
              <tr className="border-b border-[#e8ecf2] text-[11px] font-medium uppercase tracking-wide text-[#6b7280]">
                {credit.table_headers.map((header) => (
                  <th key={header} className="px-5 py-3">
                    {header}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-[#e8ecf2]">
              {credit.rows.map((row) => (
                <tr
                  key={row.component_label}
                  className={cn(
                    "text-[#172b45]",
                    row.is_total && "font-semibold",
                  )}
                >
                  <td className="px-5 py-3.5">{row.component_label}</td>
                  <td className="px-5 py-3.5 tabular-nums">{row.hours_per_week}</td>
                  <td className="px-5 py-3.5 tabular-nums">{row.credits}</td>
                  <td className="px-5 py-3.5 text-[#6b7280]">{row.assessed_by}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </StAcademicsSectionCard>
    </section>
  );
}