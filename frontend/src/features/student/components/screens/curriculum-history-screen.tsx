"use client";

import {
  StAcademicsOutcomeBadge,
  StAcademicsPageBlock,
  StAcademicsSectionCard,
} from "@/features/student/components/ui/student-academics-figma-ui";
import { QueryState } from "@/features/student/components/ui/student-screen-ui";
import { useCurriculumHistoryPage } from "@/features/student/hooks/use-student-curriculum";

export function CurriculumHistoryScreen() {
  const pageQuery = useCurriculumHistoryPage();

  return (
    <StAcademicsPageBlock
      title={pageQuery.data?.page_title ?? "Curriculum History"}
      description={pageQuery.data?.page_subtitle ?? "Versions of your curriculum"}
      figmaNode="164:10272"
    >
      <QueryState
        isLoading={pageQuery.isLoading}
        isError={pageQuery.isError}
        error={pageQuery.error}
        onRetry={() => void pageQuery.refetch()}
      >
        {pageQuery.data ? (
          <StAcademicsSectionCard
            title={pageQuery.data.panel_title}
            footer={<span>{pageQuery.data.footer_label}</span>}
          >
            {pageQuery.data.rows.length === 0 ? (
              <p className="px-5 py-10 text-center text-[13px] text-[#607086]">
                No curriculum versions have been published for your programme yet.
              </p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[720px] text-left text-[13px]">
                  <thead>
                    <tr className="border-b border-[#e8ecf2] text-[11px] font-medium uppercase tracking-wide text-[#6b7280]">
                      {pageQuery.data.table_headers.map((header) => (
                        <th key={header} className="px-5 py-3">
                          {header}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#e8ecf2]">
                    {pageQuery.data.rows.map((row) => (
                      <tr key={`${row.version_label}-${row.effective_from_label}`} className="text-[#172b45]">
                        <td className="px-5 py-3.5 font-mono text-[12px] font-semibold">{row.version_label}</td>
                        <td className="px-5 py-3.5">{row.regulation_label}</td>
                        <td className="px-5 py-3.5 text-[#6b7280]">{row.effective_from_label}</td>
                        <td className="px-5 py-3.5 font-medium">{row.change_summary}</td>
                        <td className="px-5 py-3.5">
                          <StAcademicsOutcomeBadge label={row.applies_label} tone={row.applies_tone} />
                        </td>
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
  );
}