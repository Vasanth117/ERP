"use client";

import Link from "next/link";
import type { Route } from "next";

import { ChevronRightIcon } from "@/components/icons/erp/generated/chevron-right";
import {
  StAcademicsPageBlock,
  StAcademicsSectionCard,
} from "@/features/student/components/ui/student-academics-figma-ui";
import { STUDENT_BTN_PRIMARY } from "@/features/student/components/ui/student-portal-tokens";
import { QueryState } from "@/features/student/components/ui/student-screen-ui";
import { useCurriculumCategoriesElectivesPage } from "@/features/student/hooks/use-student-curriculum";
import { cn } from "@/lib/utils";

function CategoryTable({
  title,
  headers,
  rows,
  footer,
}: {
  title: string;
  headers: string[];
  rows: { course_code: string; course_name: string; credits: number }[];
  footer: string;
}) {
  return (
    <StAcademicsSectionCard title={title} footer={<span>{footer}</span>}>
      {rows.length === 0 ? (
        <p className="px-5 py-10 text-center text-[13px] text-[#607086]">
          No {title.toLowerCase()} subjects for this semester yet.
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[280px] text-left text-[13px]">
            <thead>
              <tr className="border-b border-[#e8ecf2] text-[11px] font-medium uppercase tracking-wide text-[#6b7280]">
                {headers.map((header) => (
                  <th key={header} className="px-5 py-3">
                    {header}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-[#e8ecf2]">
              {rows.map((row) => (
                <tr key={row.course_code} className="text-[#172b45]">
                  <td className="px-5 py-3.5 font-mono text-[12px] font-semibold">{row.course_code}</td>
                  <td className="px-5 py-3.5 font-medium">{row.course_name}</td>
                  <td className="px-5 py-3.5 tabular-nums">{row.credits}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </StAcademicsSectionCard>
  );
}

export function CategoriesElectivesScreen() {
  const pageQuery = useCurriculumCategoriesElectivesPage();

  return (
    <div className="space-y-8">
      <StAcademicsPageBlock
        title={pageQuery.data?.categories_page_title ?? "Theory and Practical Subject Categories"}
        description={pageQuery.data?.categories_page_subtitle ?? "Subjects by type"}
        figmaNode="165:64048"
      >
        <QueryState
          isLoading={pageQuery.isLoading}
          isError={pageQuery.isError}
          error={pageQuery.error}
          onRetry={() => void pageQuery.refetch()}
        >
          {pageQuery.data ? (
            <div className="grid gap-5 lg:grid-cols-2">
              <CategoryTable
                title={pageQuery.data.theory_panel.panel_title}
                headers={pageQuery.data.theory_panel.table_headers}
                rows={pageQuery.data.theory_panel.rows}
                footer={pageQuery.data.theory_panel.footer_label}
              />
              <CategoryTable
                title={pageQuery.data.practical_panel.panel_title}
                headers={pageQuery.data.practical_panel.table_headers}
                rows={pageQuery.data.practical_panel.rows}
                footer={pageQuery.data.practical_panel.footer_label}
              />
            </div>
          ) : null}
        </QueryState>
      </StAcademicsPageBlock>

      <StAcademicsPageBlock
        title={pageQuery.data?.elective_page_title ?? "Elective Subject Catalogue"}
        description={pageQuery.data?.elective_page_subtitle ?? "Electives offered for your programme"}
        figmaNode="164:9959"
        actions={
          <Link
            href={(pageQuery.data?.registration_href ?? "/student/registration") as Route}
            className={cn(STUDENT_BTN_PRIMARY, "gap-1.5")}
          >
            <span>Go to registration</span>
            <ChevronRightIcon className="size-3.5 stroke-[2]" aria-hidden />
          </Link>
        }
      >
        <QueryState
          isLoading={pageQuery.isLoading}
          isError={pageQuery.isError}
          error={pageQuery.error}
          onRetry={() => void pageQuery.refetch()}
        >
          {pageQuery.data ? (
            <StAcademicsSectionCard
              title="Electives"
              footer={<span>{pageQuery.data.elective_footer_label}</span>}
            >
              {pageQuery.data.elective_rows.length === 0 ? (
                <p className="px-5 py-10 text-center text-[13px] text-[#607086]">
                  No elective subjects published for your programme yet.
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[640px] text-left text-[13px]">
                    <thead>
                      <tr className="border-b border-[#e8ecf2] text-[11px] font-medium uppercase tracking-wide text-[#6b7280]">
                        {pageQuery.data.elective_table_headers.map((header) => (
                          <th key={header} className="px-5 py-3">
                            {header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#e8ecf2]">
                      {pageQuery.data.elective_rows.map((row) => (
                        <tr key={`${row.course_code}-${row.group_label}`} className="text-[#172b45]">
                          <td className="px-5 py-3.5 font-mono text-[12px] font-semibold">{row.course_code}</td>
                          <td className="px-5 py-3.5 font-medium">{row.course_name}</td>
                          <td className="px-5 py-3.5">{row.group_label}</td>
                          <td className="px-5 py-3.5 tabular-nums">{row.credits}</td>
                          <td className="px-5 py-3.5 text-[#6b7280]">{row.offered_in_label}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </StAcademicsSectionCard>
          ) : null}
        </QueryState>
      </StAcademicsPageBlock>
    </div>
  );
}