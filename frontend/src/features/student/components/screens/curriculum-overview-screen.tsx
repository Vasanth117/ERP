"use client";

import { useCallback } from "react";
import { ArrowDownToLineIcon } from "@/components/icons/erp/generated/arrow-down-to-line";
import {
  CollegeAdminDashboardKpiCard,
  CollegeAdminKpiGrid,
} from "@/features/college-admin/components/ui/college-admin-kpi-card";
import {
  StAcademicsOutcomeBadge,
  StAcademicsPageBlock,
  StAcademicsSectionCard,
  displayOrDash,
} from "@/features/student/components/ui/student-academics-figma-ui";
import { QueryState } from "@/features/student/components/ui/student-screen-ui";
import { STUDENT_BTN_PRIMARY } from "@/features/student/components/ui/student-portal-tokens";
import { useCurriculumOverview } from "@/features/student/hooks/use-student-curriculum";
import type { CurriculumOverview } from "@/features/student/types/curriculum";

export function CurriculumOverviewScreen() {
  const { data, isLoading, isError, error, refetch } = useCurriculumOverview();

  const handleDownload = useCallback(() => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `curriculum-overview-${data.programme_code.replace(/\s+/g, "-").toLowerCase()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data]);

  return (
    <QueryState
      isLoading={isLoading}
      isError={isError}
      error={error}
      onRetry={() => void refetch()}
    >
      {data ? (
        <CurriculumOverviewContent data={data} onDownload={handleDownload} />
      ) : null}
    </QueryState>
  );
}

function CurriculumOverviewContent({
  data,
  onDownload,
}: {
  data: CurriculumOverview;
  onDownload: () => void;
}) {
  const { kpis } = data;

  return (
    <StAcademicsPageBlock
      title={data.page_title}
      description={data.programme_headline}
      figmaNode="164:7290"
      actions={
        <button type="button" onClick={onDownload} className={STUDENT_BTN_PRIMARY}>
          <ArrowDownToLineIcon className="size-3.5 stroke-[2]" aria-hidden />
          <span>Download curriculum</span>
        </button>
      }
    >
      <CollegeAdminKpiGrid className="grid-cols-2 lg:grid-cols-4">
        <CollegeAdminDashboardKpiCard
          label="Total credits"
          value={displayOrDash(kpis.total_credits)}
          hint={kpis.total_credits_semester_hint}
          index={0}
          kpiKey="st03-total-credits"
        />
        <CollegeAdminDashboardKpiCard
          label="Core subjects"
          value={displayOrDash(kpis.core_subjects)}
          index={1}
          kpiKey="st03-core-subjects"
        />
        <CollegeAdminDashboardKpiCard
          label="Electives"
          value={displayOrDash(kpis.electives)}
          hint={kpis.elective_credits_hint}
          index={2}
          kpiKey="st03-electives"
        />
        <CollegeAdminDashboardKpiCard
          label="Labs"
          value={displayOrDash(kpis.labs)}
          index={3}
          kpiKey="st03-labs"
        />
      </CollegeAdminKpiGrid>

      <StAcademicsSectionCard
        title="Semesters"
        footer={<span>{data.semesters_footer_label}</span>}
      >
        <div className="overflow-x-auto">
          <table className="w-full min-w-[560px] text-left text-[13px]">
            <thead>
              <tr className="border-b border-[#e8ecf2] text-[11px] font-medium uppercase tracking-wide text-[#6b7280]">
                <th className="px-5 py-3 font-medium">Semester</th>
                <th className="px-5 py-3 font-medium">Subjects</th>
                <th className="px-5 py-3 font-medium">Credits</th>
                <th className="px-5 py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#e8ecf2]">
              {data.semesters.map((row) => (
                <tr key={row.semester_number} className="text-[#172b45]">
                  <td className="px-5 py-3.5 font-semibold">{row.label}</td>
                  <td className="px-5 py-3.5 tabular-nums">{row.subject_count}</td>
                  <td className="px-5 py-3.5 tabular-nums">{row.credits}</td>
                  <td className="px-5 py-3.5">
                    <StAcademicsOutcomeBadge label={row.status_label} tone={row.status_tone} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </StAcademicsSectionCard>
    </StAcademicsPageBlock>
  );
}