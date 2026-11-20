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
  "hostel-building-management",
  "room-management",
  "bed-allocation",
  "hostel-admission-applications",
  "resident-management",
  "hostel-check-in-checkout",
  "hostel-fee-management",
  "mess-management",
  "visitor-management",
  "leave-outpass-approval",
  "maintenance-complaints",
  "hostel-incident-management",
  "hostel-settings",
]);

export function HostelScreen({ slug, title }: { slug: string; title: string }) {
  const { apiPath, viewType } = resolveModuleEndpoint("hostel", slug);
  if (slug === "hostel-dashboard") {
    return <HostelDashboard />;
  }
  if (slug === "hostel-reports") {
    return (
      <GenericModuleScreen
        moduleKey="hostel"
        slug={slug}
        title={title}
        apiPath="/college-admin/hostel-administration/reports/occupancy"
        viewType="report"
      />
    );
  }
  if (FORM_SLUGS.has(slug)) {
    return (
      <FormPlaceholder title={title} description="Hostel administration workflow (Figma CA 13)." />
    );
  }
  return (
    <GenericModuleScreen
      moduleKey="hostel"
      slug={slug}
      title={title}
      apiPath={apiPath}
      viewType={viewType}
    />
  );
}

function HostelDashboard() {
  const occupancy = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "hostel-occupancy"],
    queryFn: () =>
      apiRequest<Record<string, unknown>>("/college-admin/hostel-administration/reports/occupancy"),
  });
  const waiting = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "hostel-waiting"],
    queryFn: () =>
      apiRequest<{ items?: unknown[]; total?: number }>(
        "/college-admin/hostel-administration/waiting-list?limit=25&offset=0",
      ),
  });
  const rows = rowsFromApi(waiting.data?.items);
  return (
    <QueryState
      isLoading={occupancy.isLoading}
      isError={occupancy.isError}
      error={occupancy.error}
      onRetry={() => void occupancy.refetch()}
    >
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Occupancy" value={String(occupancy.data?.occupancy_rate ?? "—")} />
        <StatCard label="Waiting list" value={waiting.data?.total ?? rows.length} />
        <Link
          href="/college-admin/hostel/hostel-admission-applications"
          className="text-sm font-medium text-[#245dd8]"
        >
          Applications →
        </Link>
        <Link href="/college-admin/hostel/hostel-reports" className="text-sm font-medium text-[#245dd8]">
          Reports →
        </Link>
      </div>
      <SectionPanel title="Waiting list" className="mt-6">
        <ToolbarRow onRefresh={() => void waiting.refetch()} />
        <DataTable columns={columnsFromRows(rows)} rows={rows} />
      </SectionPanel>
    </QueryState>
  );
}