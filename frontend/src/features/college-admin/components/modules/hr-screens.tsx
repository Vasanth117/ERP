"use client";

import Link from "next/link";
import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

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
  "employee-management",
  "recruitment-management",
  "employee-onboarding",
  "leave-approval",
  "salary-structure-management",
  "payroll-processing",
  "salary-slip-management",
  "employee-benefits-claims",
  "performance-management",
  "hr-settings-policies",
]);

export function HrScreen({ slug, title }: { slug: string; title: string }) {
  const { apiPath, viewType } = resolveModuleEndpoint("hr", slug);
  if (slug === "hr-dashboard") {
    return <HrDashboard />;
  }
  if (slug === "leave-management" || slug === "employee-attendance") {
    return (
      <GenericModuleScreen
        moduleKey="hr"
        slug={slug}
        title={title}
        apiPath="/college-admin/hr-administration/leave/pending"
        viewType="list"
      />
    );
  }
  if (slug === "hr-reports") {
    return (
      <GenericModuleScreen
        moduleKey="hr"
        slug={slug}
        title={title}
        apiPath="/college-admin/hr-administration/reports/summary"
        viewType="report"
      />
    );
  }
  if (FORM_SLUGS.has(slug)) {
    return <FormPlaceholder title={title} description="HR administration workflow (Figma CA 11)." />;
  }
  return (
    <GenericModuleScreen
      moduleKey="hr"
      slug={slug}
      title={title}
      apiPath={apiPath}
      viewType={viewType}
    />
  );
}

function HrDashboard() {
  const stats = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "hr-stats"],
    queryFn: () => apiRequest<Record<string, unknown>>("/college-admin/hr-administration/statistics"),
  });
  const leave = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "hr-leave"],
    queryFn: () =>
      apiRequest<{ total?: number; items?: unknown[] }>(
        "/college-admin/hr-administration/leave/pending?limit=20&offset=0",
      ),
  });
  const rows = rowsFromApi(leave.data?.items);
  return (
    <QueryState
      isLoading={stats.isLoading}
      isError={stats.isError}
      error={stats.error}
      onRetry={() => void stats.refetch()}
    >
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Staff metric" value={String(stats.data?.headcount ?? "—")} />
        <StatCard label="Pending leave" value={leave.data?.total ?? rows.length} />
        <Link href="/college-admin/hr/leave-management" className="text-sm font-medium text-[#245dd8]">
          Leave management →
        </Link>
        <Link href="/college-admin/hr/hr-reports" className="text-sm font-medium text-[#245dd8]">
          HR reports →
        </Link>
      </div>
      <SectionPanel title="Pending leave requests" className="mt-6">
        <ToolbarRow onRefresh={() => void leave.refetch()} />
        <DataTable columns={columnsFromRows(rows)} rows={rows} />
      </SectionPanel>
    </QueryState>
  );
}