"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { apiRequest } from "@/lib/api/client";
import {
  DataTable,
  DetailGrid,
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

const LIST_SLUGS: Record<string, string> = {
  "administrative-audit-logs": "/college-admin/security-administration/audit-logs",
  "user-activity-logs": "/college-admin/security-administration/audit-logs",
  "login-history": "/college-admin/security-administration/login-activity",
  "security-events": "/college-admin/security-administration/security-events",
  "failed-login-monitoring": "/college-admin/security-administration/login-activity",
};

const FORM_SLUGS = new Set([
  "permission-access-review",
  "session-management",
  "password-authentication-policies",
]);

export function SecurityScreen({ slug, title }: { slug: string; title: string }) {
  const { apiPath, viewType } = resolveModuleEndpoint("security", slug);
  if (slug === "security-dashboard") {
    return <SecurityDashboard />;
  }
  if (slug === "security-reports") {
    return (
      <GenericModuleScreen
        moduleKey="security"
        slug={slug}
        title={title}
        apiPath="/college-admin/security-administration/reports/summary"
        viewType="report"
      />
    );
  }
  if (slug === "audit-log-details") {
    return <AuditLogDetail title={title} />;
  }
  if (LIST_SLUGS[slug]) {
    return (
      <GenericModuleScreen
        moduleKey="security"
        slug={slug}
        title={title}
        apiPath={LIST_SLUGS[slug]}
        viewType="list"
      />
    );
  }
  if (FORM_SLUGS.has(slug)) {
    return (
      <GenericModuleScreen
        moduleKey="security"
        slug={slug}
        title={title}
        apiPath="/college-admin/security-administration/policies"
        viewType="settings"
      />
    );
  }
  return (
    <GenericModuleScreen
      moduleKey="security"
      slug={slug}
      title={title}
      apiPath={apiPath}
      viewType={viewType}
    />
  );
}

function SecurityDashboard() {
  const summary = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "security-summary"],
    queryFn: () =>
      apiRequest<Record<string, unknown>>(
        "/college-admin/security-administration/reports/summary",
      ),
  });
  const events = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "security-events"],
    queryFn: () =>
      apiRequest<{ items?: unknown[]; total?: number }>(
        "/college-admin/security-administration/security-events?limit=20&offset=0",
      ),
  });
  const rows = rowsFromApi(events.data?.items);
  return (
    <QueryState
      isLoading={summary.isLoading}
      isError={summary.isError}
      error={summary.error}
      onRetry={() => void summary.refetch()}
    >
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Security events" value={events.data?.total ?? rows.length} />
        <StatCard label="Open issues" value={String(summary.data?.open_events ?? "—")} />
        <Link
          href="/college-admin/security/administrative-audit-logs"
          className="text-sm font-medium text-[#245dd8]"
        >
          Audit logs →
        </Link>
        <Link href="/college-admin/security/security-reports" className="text-sm font-medium text-[#245dd8]">
          Security reports →
        </Link>
      </div>
      <SectionPanel title="Recent security events" className="mt-6">
        <ToolbarRow onRefresh={() => void events.refetch()} />
        <DataTable columns={columnsFromRows(rows)} rows={rows} />
      </SectionPanel>
    </QueryState>
  );
}

function AuditLogDetail({ title }: { title: string }) {
  const params = useSearchParams();
  const id = params.get("id") ?? "";
  const q = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "audit-log", id],
    queryFn: () =>
      apiRequest<{ items?: unknown[] }>(
        `/college-admin/security-administration/audit-logs?limit=1&offset=0`,
      ),
    enabled: Boolean(id),
  });
  const rows = rowsFromApi(q.data?.items);
  if (!id) {
    return (
      <SectionPanel title={title}>
        <Link href="/college-admin/security/administrative-audit-logs" className="text-sm text-[#245dd8]">
          Browse audit logs
        </Link>
      </SectionPanel>
    );
  }
  return (
    <QueryState isLoading={q.isLoading} isError={q.isError} error={q.error} onRetry={() => void q.refetch()}>
      <SectionPanel title={title}>
        <DetailGrid record={rows[0] ?? { log_id: id }} />
      </SectionPanel>
    </QueryState>
  );
}