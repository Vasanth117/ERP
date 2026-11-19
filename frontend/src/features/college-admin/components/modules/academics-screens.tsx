"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import {
  fetchAcademicTerms,
  fetchAcademicYears,
  fetchConfigHistory,
  fetchProgrammes,
} from "@/features/college-admin/api/academics";
import {
  DataTable,
  FormPlaceholder,
  SectionPanel,
  ToolbarRow,
  columnsFromRows,
  rowsFromApi,
} from "@/features/college-admin/components/ui/college-admin-screen-ui";
import {
  QueryState,
  StatCard,
} from "@/features/college-admin/components/ui/query-state";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function AcademicsScreen({ slug }: { slug: string }) {
  switch (slug) {
    case "academic-configuration-dashboard":
      return <AcademicsDashboard />;
    case "academic-year-management":
      return <YearsList />;
    case "semester-management":
      return <TermsList />;
    case "programme-management":
      return <ProgrammesList />;
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
      return <AcademicsDashboard />;
  }
}

function AcademicsDashboard() {
  const years = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "academic-years"],
    queryFn: fetchAcademicYears,
  });
  const programmes = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "programmes"],
    queryFn: fetchProgrammes,
  });

  const loading = years.isLoading || programmes.isLoading;
  const error = years.error ?? programmes.error;

  return (
    <QueryState
      isLoading={loading}
      isError={Boolean(error)}
      error={error as Error}
      onRetry={() => {
        void years.refetch();
        void programmes.refetch();
      }}
    >
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Academic years" value={years.data?.length ?? 0} />
        <StatCard label="Programmes" value={programmes.data?.length ?? 0} />
        <StatCard
          label="Current year"
          value={
            years.data?.find((y) => y.is_current)?.label ??
            years.data?.[0]?.label ??
            "—"
          }
        />
        <Link
          href="/college-admin/academics/academic-year-management"
          className="flex items-center rounded-xl border border-[#dce3ec] bg-white p-4 text-sm font-medium text-[#245dd8] shadow-[0px_1px_1px_rgba(23,43,69,0.04)]"
        >
          Manage academic years →
        </Link>
      </div>
    </QueryState>
  );
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

function ProgrammesList() {
  const q = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "programmes-list"],
    queryFn: fetchProgrammes,
  });
  const rows = rowsFromApi(q.data);
  return <ListSection title="Programmes" q={q} rows={rows} />;
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