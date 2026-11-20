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
  "attendance-configuration",
  "attendance-approval",
]);

export function AttendanceScreen({ slug, title }: { slug: string; title: string }) {
  const { apiPath, viewType } = resolveModuleEndpoint("attendance", slug);
  if (slug === "attendance-dashboard") {
    return <AttendanceDashboard />;
  }
  if (FORM_SLUGS.has(slug)) {
    return (
      <FormPlaceholder title={title} description="Attendance configuration aligned with Figma CA 08." />
    );
  }
  return (
    <GenericModuleScreen
      moduleKey="attendance"
      slug={slug}
      title={title}
      apiPath={apiPath}
      viewType={viewType}
    />
  );
}

function AttendanceDashboard() {
  const dept = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "attendance-dept-summary"],
    queryFn: () =>
      apiRequest<unknown[]>("/college-admin/attendance-administration/summaries/departments"),
  });
  const missing = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "attendance-missing"],
    queryFn: () =>
      apiRequest<{ total?: number }>(
        "/college-admin/attendance-administration/submissions/missing?limit=1&offset=0",
      ),
  });
  return (
    <QueryState
      isLoading={dept.isLoading}
      isError={dept.isError}
      error={dept.error}
      onRetry={() => void dept.refetch()}
    >
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Departments tracked" value={rowsFromApi(dept.data).length} />
        <StatCard label="Missing submissions" value={missing.data?.total ?? 0} />
        <Link
          href="/college-admin/attendance/attendance-correction-requests"
          className="flex items-center text-sm font-medium text-[#245dd8]"
        >
          Correction requests →
        </Link>
        <Link
          href="/college-admin/attendance/attendance-rules-policies"
          className="flex items-center text-sm font-medium text-[#245dd8]"
        >
          Rules & policies →
        </Link>
      </div>
      <SectionPanel title="Department summaries" className="mt-6">
        <ToolbarRow onRefresh={() => void dept.refetch()} />
        <DataTable
          columns={columnsFromRows(rowsFromApi(dept.data))}
          rows={rowsFromApi(dept.data)}
        />
      </SectionPanel>
    </QueryState>
  );
}