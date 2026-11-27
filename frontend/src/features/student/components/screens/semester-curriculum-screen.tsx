"use client";

import Link from "next/link";
import { useCallback, useState } from "react";
import type { Route } from "next";

import {
  StAcademicsOutcomeBadge,
  StAcademicsPageBlock,
  StAcademicsSectionCard,
} from "@/features/student/components/ui/student-academics-figma-ui";
import { PORTAL_CARD, STUDENT_TEXT_MUTED } from "@/features/student/components/ui/student-portal-tokens";
import { QueryState } from "@/features/student/components/ui/student-screen-ui";
import { useCurriculumSemesterPage } from "@/features/student/hooks/use-student-curriculum";
import type { CurriculumSemesterPage } from "@/features/student/types/curriculum";
import { cn } from "@/lib/utils";

export function SemesterCurriculumScreen() {
  const [semester, setSemester] = useState<number | undefined>(undefined);
  const { data, isLoading, isError, error, refetch, isFetching } = useCurriculumSemesterPage(semester);

  const activeSemester = data?.selected_semester ?? 1;

  const onSelectSemester = useCallback((n: number) => {
    setSemester(n);
  }, []);

  return (
    <QueryState
      isLoading={isLoading || (isFetching && !data)}
      isError={isError}
      error={error}
      onRetry={() => void refetch()}
    >
      {data ? (
        <SemesterCurriculumContent
          data={data}
          activeSemester={activeSemester}
          onSelectSemester={onSelectSemester}
          isFetching={isFetching}
        />
      ) : null}
    </QueryState>
  );
}

function SemesterCurriculumContent({
  data,
  activeSemester,
  onSelectSemester,
  isFetching,
}: {
  data: CurriculumSemesterPage;
  activeSemester: number;
  onSelectSemester: (n: number) => void;
  isFetching: boolean;
}) {
  return (
    <StAcademicsPageBlock
      title={data.page_title}
      description={data.programme_headline}
      figmaNode="164:7641"
      actions={
        <StAcademicsOutcomeBadge label={data.semester_status_label} tone={data.semester_status_tone} />
      }
    >
      {data.semester_tabs.length > 0 ? (
        <div className={cn(PORTAL_CARD, "flex flex-wrap gap-1 bg-[#f9fafb] p-1")}>
          {data.semester_tabs.map((tab) => {
            const selected = tab.semester_number === activeSemester;
            return (
              <button
                key={tab.semester_number}
                type="button"
                disabled={isFetching && selected}
                onClick={() => onSelectSemester(tab.semester_number)}
                className={cn(
                  "rounded-md px-3 py-1.5 text-[13px] font-medium transition-colors",
                  selected
                    ? "bg-white text-[#2563eb] shadow-sm"
                    : "text-[#6b7280] hover:text-[#111827]",
                )}
              >
                {tab.tab_label}
              </button>
            );
          })}
        </div>
      ) : null}

      <StAcademicsSectionCard
        title={data.courses_panel_title}
        footer={<span>{data.courses_footer_label}</span>}
      >
        <p className={cn("border-b px-5 py-2.5 text-[12px]", STUDENT_TEXT_MUTED)}>
          {data.courses_panel_meta}
        </p>
        {data.courses.length === 0 ? (
          <p className="px-5 py-10 text-center text-[13px] text-[#607086]">
            No courses are published for this semester yet.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[36rem] text-left text-[13px]">
              <thead>
                <tr className="border-b border-[#e8ecf2] text-[11px] font-medium uppercase tracking-wide text-[#6b7280]">
                  {data.table_headers.map((header) => (
                    <th key={header} className="px-5 py-3">
                      {header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#e8ecf2]">
                {data.courses.map((row) => (
                  <tr key={row.course_id} className="text-[#172b45]">
                    <td className="px-5 py-3.5">
                      <Link href={row.syllabus_href as Route} className="hover:text-[#2563eb]">
                        <span className="font-mono text-[12px] text-[#6b7280]">{row.course_code}</span>
                        <span className="mt-0.5 block font-medium">{row.course_name}</span>
                      </Link>
                    </td>
                    <td className="px-5 py-3.5">{row.type_label}</td>
                    <td className="px-5 py-3.5 font-mono text-[12px]">{row.ltp_label}</td>
                    <td className="px-5 py-3.5 tabular-nums">{row.credits}</td>
                    <td className="px-5 py-3.5">
                      <StAcademicsOutcomeBadge label={row.status_label} tone={row.status_tone} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </StAcademicsSectionCard>
    </StAcademicsPageBlock>
  );
}