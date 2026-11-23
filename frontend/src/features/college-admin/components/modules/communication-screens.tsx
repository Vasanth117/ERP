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
  "announcements-management",
  "create-announcement",
  "student-notifications",
  "faculty-notifications",
  "parent-communication",
  "email-communication",
  "sms-communication",
  "whatsapp-communication",
  "communication-templates",
  "scheduled-messages",
]);

export function CommunicationScreen({ slug, title }: { slug: string; title: string }) {
  const { apiPath, viewType } = resolveModuleEndpoint("communication", slug);
  if (slug === "communication-dashboard") {
    return <CommunicationDashboard />;
  }
  if (slug === "delivery-status-monitoring" || slug === "communication-history") {
    return (
      <GenericModuleScreen
        moduleKey="communication"
        slug={slug}
        title={title}
        apiPath="/college-admin/communication-administration/deliveries/failed"
        viewType="list"
      />
    );
  }
  if (FORM_SLUGS.has(slug)) {
    return (
      <FormPlaceholder
        title={title}
        description="Institutional communication workflow (Figma CA 14)."
      />
    );
  }
  return (
    <GenericModuleScreen
      moduleKey="communication"
      slug={slug}
      title={title}
      apiPath={apiPath}
      viewType={viewType}
    />
  );
}

function CommunicationDashboard() {
  const summary = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "comm-summary"],
    queryFn: () =>
      apiRequest<Record<string, unknown>>(
        "/college-admin/communication-administration/reports/summary",
      ),
  });
  const failed = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "comm-failed"],
    queryFn: () =>
      apiRequest<{ items?: unknown[]; total?: number }>(
        "/college-admin/communication-administration/deliveries/failed?limit=25&offset=0",
      ),
  });
  const rows = rowsFromApi(failed.data?.items);
  return (
    <QueryState
      isLoading={summary.isLoading}
      isError={summary.isError}
      error={summary.error}
      onRetry={() => void summary.refetch()}
    >
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Messages sent" value={String(summary.data?.sent_count ?? "—")} />
        <StatCard label="Failed deliveries" value={failed.data?.total ?? rows.length} />
        <Link
          href="/college-admin/communication/create-announcement"
          className="text-sm font-medium text-[#245dd8]"
        >
          Create announcement →
        </Link>
        <Link
          href="/college-admin/communication/delivery-status-monitoring"
          className="text-sm font-medium text-[#245dd8]"
        >
          Delivery status →
        </Link>
      </div>
      <SectionPanel title="Failed deliveries" className="mt-6">
        <ToolbarRow onRefresh={() => void failed.refetch()} />
        <DataTable columns={columnsFromRows(rows)} rows={rows} />
      </SectionPanel>
    </QueryState>
  );
}