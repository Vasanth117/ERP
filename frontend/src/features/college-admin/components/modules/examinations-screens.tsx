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

const FORM_SLUGS = new Set([
  "examination-session-management",
  "examination-configuration",
  "exam-timetable-management",
  "exam-registration-management",
  "examination-hall-seating-management",
  "invigilator-allocation",
  "marks-entry-management",
  "internal-external-assessment",
  "result-processing",
  "result-approval",
  "result-publication",
  "revaluation-management",
  "supplementary-examination-management",
  "hall-ticket-administration",
]);

export function ExaminationsScreen({ slug, title }: { slug: string; title: string }) {
  const { apiPath, viewType } = resolveModuleEndpoint("examinations", slug);
  if (slug === "examination-dashboard") {
    return <ExaminationDashboard />;
  }
  if (FORM_SLUGS.has(slug)) {
    return (
      <FormPlaceholder title={title} description="Examination administration workflow (Figma CA 09)." />
    );
  }
  return (
    <GenericModuleScreen
      moduleKey="examinations"
      slug={slug}
      title={title}
      apiPath={apiPath}
      viewType={viewType}
    />
  );
}

function ExaminationDashboard() {
  const pending = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "exam-pending-marks"],
    queryFn: () =>
      apiRequest<{ total?: number; items?: unknown[] }>(
        "/college-admin/examination-administration/marks/pending?limit=50&offset=0",
      ),
  });
  const rows = rowsFromApi(pending.data?.items);
  return (
    <QueryState
      isLoading={pending.isLoading}
      isError={pending.isError}
      error={pending.error}
      onRetry={() => void pending.refetch()}
    >
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <StatCard label="Pending mark reviews" value={pending.data?.total ?? rows.length} />
        <Link
          href="/college-admin/examinations/student-exam-eligibility"
          className="flex items-center text-sm font-medium text-[#245dd8]"
        >
          Eligibility registry →
        </Link>
        <Link
          href="/college-admin/examinations/examination-reports"
          className="flex items-center text-sm font-medium text-[#245dd8]"
        >
          Reports →
        </Link>
      </div>
      <SectionPanel title="Pending evaluations" className="mt-6">
        <ToolbarRow onRefresh={() => void pending.refetch()} />
        <DataTable columns={columnsFromRows(rows)} rows={rows} />
      </SectionPanel>
    </QueryState>
  );
}