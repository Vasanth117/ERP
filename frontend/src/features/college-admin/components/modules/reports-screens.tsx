"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { apiRequest } from "@/lib/api/client";
import {
  DataTable,
  FormPlaceholder,
  SectionPanel,
  ToolbarRow,
  columnsFromRows,
  rowsFromApi,
} from "@/features/college-admin/components/ui/college-admin-screen-ui";
import { GenericModuleScreen } from "@/features/college-admin/components/modules/generic-module-screen";
import {
  QueryState,
  StatCard,
} from "@/features/college-admin/components/ui/query-state";
import { resolveModuleEndpoint } from "@/features/college-admin/config/module-endpoint-resolver";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

const REPORT_SLUGS = new Set([
  "student-reports",
  "faculty-employee-reports",
  "department-reports",
  "academic-performance-reports",
  "attendance-reports",
  "examination-reports",
  "finance-reports",
  "hr-reports",
  "library-reports",
  "hostel-reports",
]);

const FORM_SLUGS = new Set([
  "custom-report-builder",
  "scheduled-reports",
]);

export function ReportsScreen({ slug, title }: { slug: string; title: string }) {
  const { apiPath, viewType } = resolveModuleEndpoint("reports", slug);
  if (slug === "reports-dashboard") {
    return <ReportsDashboard />;
  }
  if (slug === "export-download-history") {
    return (
      <GenericModuleScreen
        moduleKey="reports"
        slug={slug}
        title={title}
        apiPath="/college-admin/reports-analytics/exports/download"
        viewType="report"
      />
    );
  }
  if (REPORT_SLUGS.has(slug)) {
    return (
      <GenericModuleScreen
        moduleKey="reports"
        slug={slug}
        title={title}
        apiPath="/college-admin/reports-analytics/definitions"
        viewType="report"
      />
    );
  }
  if (FORM_SLUGS.has(slug)) {
    return (
      <FormPlaceholder
        title={title}
        description="Custom and scheduled reporting (Figma CA 16)."
        submitLabel="Save schedule"
      />
    );
  }
  return (
    <GenericModuleScreen
      moduleKey="reports"
      slug={slug}
      title={title}
      apiPath={apiPath}
      viewType={viewType}
    />
  );
}

function ReportsDashboard() {
  const dash = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "reports-dashboard"],
    queryFn: () =>
      apiRequest<Record<string, unknown>>("/college-admin/reports-analytics/dashboard"),
  });
  const jobs = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "report-jobs"],
    queryFn: () =>
      apiRequest<{ items?: unknown[]; total?: number }>(
        "/college-admin/reports-analytics/jobs?limit=25&offset=0",
      ),
  });
  const defs = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "report-defs"],
    queryFn: () =>
      apiRequest<unknown[]>("/college-admin/reports-analytics/definitions"),
  });
  const jobRows = rowsFromApi(jobs.data?.items);
  const defRows = rowsFromApi(defs.data);
  return (
    <QueryState
      isLoading={dash.isLoading}
      isError={dash.isError}
      error={dash.error}
      onRetry={() => void dash.refetch()}
    >
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Report definitions" value={defRows.length} />
        <StatCard label="Active jobs" value={jobs.data?.total ?? jobRows.length} />
        <Link
          href="/college-admin/reports/custom-report-builder"
          className="text-sm font-medium text-[#245dd8]"
        >
          Custom builder →
        </Link>
        <Link
          href="/college-admin/reports/export-download-history"
          className="text-sm font-medium text-[#245dd8]"
        >
          Export history →
        </Link>
      </div>
      <SectionPanel title="Recent report jobs" className="mt-6">
        <ToolbarRow
          onRefresh={() => {
            void jobs.refetch();
            void defs.refetch();
          }}
        />
        <DataTable columns={columnsFromRows(jobRows)} rows={jobRows} />
      </SectionPanel>
    </QueryState>
  );
}