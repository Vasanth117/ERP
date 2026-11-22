"use client";

import Link from "next/link";
import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { apiRequest } from "@/lib/api/client";
import {
  FormPlaceholder,
  SectionPanel,
  ToolbarRow,
} from "@/features/college-admin/components/ui/college-admin-screen-ui";
import { GenericModuleScreen } from "@/features/college-admin/components/modules/generic-module-screen";
import {
  CollegeAdminKpiGrid,
  QueryState,
  StatCard,
} from "@/features/college-admin/components/ui/query-state";
import { resolveModuleEndpoint } from "@/features/college-admin/config/module-endpoint-resolver";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

const FORM_SLUGS = new Set([
  "campus-asset-management",
  "building-infrastructure-management",
  "classroom-management",
  "laboratory-management",
  "equipment-inventory",
  "maintenance-requests",
  "maintenance-work-orders",
  "vendor-service-provider-management",
  "procurement-requests",
  "transport-fleet-management",
  "vehicle-management",
  "campus-facility-booking",
  "security-visitor-management",
]);

export function OperationsScreen({ slug, title }: { slug: string; title: string }) {
  const { apiPath, viewType } = resolveModuleEndpoint("operations", slug);
  if (slug === "operations-dashboard") {
    return <OperationsDashboard />;
  }
  if (slug === "institutional-operations-reports") {
    return (
      <GenericModuleScreen
        moduleKey="operations"
        slug={slug}
        title={title}
        apiPath="/college-admin/operations-extensions/reports/summary"
        viewType="report"
      />
    );
  }
  if (FORM_SLUGS.has(slug)) {
    return (
      <FormPlaceholder
        title={title}
        description="Campus operations workflow (Figma CA 23). Submits via /college-admin/operations-extensions/* APIs."
      />
    );
  }
  return (
    <GenericModuleScreen
      moduleKey="operations"
      slug={slug}
      title={title}
      apiPath={apiPath}
      viewType={viewType}
    />
  );
}

function OperationsDashboard() {
  const summary = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "operations-summary"],
    queryFn: () =>
      apiRequest<Record<string, unknown>>(
        "/college-admin/operations-extensions/reports/summary",
      ),
  });
  const opsDash = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "college-ops-dash"],
    queryFn: () =>
      apiRequest<Record<string, unknown>>("/college-admin/dashboard/operations"),
  });
  return (
    <QueryState
      isLoading={summary.isLoading}
      isError={summary.isError}
      error={summary.error}
      onRetry={() => void summary.refetch()}
    >
      <CollegeAdminKpiGrid columns={4}>
        <StatCard
          label="Open maintenance"
          value={String(summary.data?.open_maintenance ?? "—")}
          kpiKey="open_maintenance"
        />
        <StatCard
          label="Assets tracked"
          value={String(summary.data?.asset_count ?? "—")}
          kpiKey="assets_tracked"
        />
        <StatCard
          label="Facilities"
          value={String(opsDash.data?.facility_bookings ?? summary.data?.facility_count ?? "—")}
          kpiKey="facilities"
        />
        <Link
          href="/college-admin/operations/maintenance-requests"
          className="flex min-h-[7.75rem] items-center rounded-[18px] border border-[#dce3ec] bg-white px-4 text-sm font-semibold text-[#245dd8] shadow-[0_2px_8px_rgba(15,23,42,0.04)] hover:bg-[#f4f8ff]"
        >
          Maintenance →
        </Link>
      </CollegeAdminKpiGrid>
      <SectionPanel title="Operations overview" className="mt-6">
        <ToolbarRow onRefresh={() => void summary.refetch()} />
        <p className="text-sm text-[#607086]">
          Institutional operations extensions cover assets, facilities, maintenance, fleet, and booking per Figma CA 23.
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          <Link
            href="/college-admin/operations/campus-asset-management"
            className="inline-flex h-9 items-center rounded-md border border-[#dce3ec] px-3 text-xs font-medium text-[#172b45]"
          >
            Assets
          </Link>
          <Link
            href="/college-admin/operations/institutional-operations-reports"
            className="inline-flex h-9 items-center rounded-md border border-[#dce3ec] px-3 text-xs font-medium text-[#172b45]"
          >
            Reports
          </Link>
        </div>
      </SectionPanel>
    </QueryState>
  );
}