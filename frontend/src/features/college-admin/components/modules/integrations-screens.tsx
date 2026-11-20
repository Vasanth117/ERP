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
  "payment-gateway-configuration",
  "email-provider-configuration",
  "sms-provider-configuration",
  "whatsapp-integration",
  "authentication-integration",
  "external-erp-integration",
  "webhook-management",
  "api-configuration",
  "connection-testing",
]);

export function IntegrationsScreen({ slug, title }: { slug: string; title: string }) {
  const { apiPath, viewType } = resolveModuleEndpoint("integrations", slug);
  if (slug === "integration-dashboard") {
    return <IntegrationsDashboard />;
  }
  if (slug === "available-integrations") {
    return (
      <GenericModuleScreen
        moduleKey="integrations"
        slug={slug}
        title={title}
        apiPath="/college-admin/integration-administration/integrations"
        viewType="list"
      />
    );
  }
  if (slug === "integration-error-monitoring" || slug === "integration-logs") {
    return (
      <GenericModuleScreen
        moduleKey="integrations"
        slug={slug}
        title={title}
        apiPath="/college-admin/integration-administration/integrations"
        viewType="report"
      />
    );
  }
  if (FORM_SLUGS.has(slug)) {
    return (
      <FormPlaceholder title={title} description="Integration connector setup (Figma CA 20)." />
    );
  }
  return (
    <GenericModuleScreen
      moduleKey="integrations"
      slug={slug}
      title={title}
      apiPath={apiPath}
      viewType={viewType}
    />
  );
}

function IntegrationsDashboard() {
  const list = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "integrations"],
    queryFn: () =>
      apiRequest<unknown[]>("/college-admin/integration-administration/integrations"),
  });
  const rows = rowsFromApi(list.data);
  return (
    <QueryState
      isLoading={list.isLoading}
      isError={list.isError}
      error={list.error}
      onRetry={() => void list.refetch()}
    >
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Registered integrations" value={rows.length} />
        <Link
          href="/college-admin/integrations/available-integrations"
          className="text-sm font-medium text-[#245dd8]"
        >
          Browse catalog →
        </Link>
        <Link
          href="/college-admin/integrations/connection-testing"
          className="text-sm font-medium text-[#245dd8]"
        >
          Test connections →
        </Link>
        <Link
          href="/college-admin/integrations/integration-logs"
          className="text-sm font-medium text-[#245dd8]"
        >
          Integration logs →
        </Link>
      </div>
      <SectionPanel title="Integration registry" className="mt-6">
        <ToolbarRow onRefresh={() => void list.refetch()} />
        <DataTable columns={columnsFromRows(rows)} rows={rows} />
      </SectionPanel>
    </QueryState>
  );
}