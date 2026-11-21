"use client";

import { useQuery } from "@tanstack/react-query";

import { AcademicConfigurationDashboard } from "@/features/college-admin/components/academics/academic-configuration-dashboard";
import { AcademicYearManagementDashboard } from "@/features/college-admin/components/academics/academic-year-management-dashboard";
import { ProgrammeManagementDashboard } from "@/features/college-admin/components/academics/programme-management-dashboard";
import { SemesterManagementDashboard } from "@/features/college-admin/components/academics/semester-management-dashboard";
import {
  fetchAcademicTerms,
  fetchAcademicYears,
  fetchConfigHistory,
} from "@/features/college-admin/api/academics";
import {
  DataTable,
  FormPlaceholder,
  SectionPanel,
  ToolbarRow,
  columnsFromRows,
  rowsFromApi,
} from "@/features/college-admin/components/ui/college-admin-screen-ui";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function AcademicsScreen({ slug }: { slug: string }) {
  switch (slug) {
    case "academic-configuration-dashboard":
      return <AcademicConfigurationDashboard />;
    case "academic-year-management":
      return <AcademicYearManagementDashboard />;
    case "semester-management":
      return <SemesterManagementDashboard />;
    case "programme-management":
      return <ProgrammeManagementDashboard />;
    case "academic-configuration-history":
      return <ConfigHistory />;
    case "course-configuration":
    case "curriculum-management":
    case "subject-management":
    case "credit-configuration":
    case "regulation-management":
    case "grading-system-configuration":
    case "academic-calendar-configuration":
    case "batch-section-configuration":
      return (
        <FormPlaceholder
          title={slug.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
          description="Academic configuration form aligned with the Figma frame layout. API publish endpoints are wired on the backend."
        />
      );
    default:
      return <AcademicConfigurationDashboard />;
  }
}

function YearsList() {
  const q = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "academic-years-list"],
    queryFn: fetchAcademicYears,
  });
  const rows = rowsFromApi(q.data);
  return (
    <ListSection title="Academic years" q={q} rows={rows} />
  );
}

function TermsList() {
  const q = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "academic-terms"],
    queryFn: () => fetchAcademicTerms(),
  });
  const rows = rowsFromApi(q.data);
  return <ListSection title="Semesters & terms" q={q} rows={rows} />;
}

function ConfigHistory() {
  const q = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "academic-config-history"],
    queryFn: fetchConfigHistory,
  });
  const rows = rowsFromApi(q.data);
  return <ListSection title="Configuration history" q={q} rows={rows} />;
}

function ListSection({
  title,
  q,
  rows,
}: {
  title: string;
  q: { isLoading: boolean; isError: boolean; error: Error | null; refetch: () => void };
  rows: Record<string, unknown>[];
}) {
  const cols = columnsFromRows(rows);
  return (
    <QueryState
      isLoading={q.isLoading}
      isError={q.isError}
      error={q.error}
      isEmpty={!q.isLoading && rows.length === 0}
      onRetry={() => void q.refetch()}
    >
      <SectionPanel title={title}>
        <ToolbarRow onRefresh={() => void q.refetch()} />
        <DataTable columns={cols} rows={rows} />
      </SectionPanel>
    </QueryState>
  );
}