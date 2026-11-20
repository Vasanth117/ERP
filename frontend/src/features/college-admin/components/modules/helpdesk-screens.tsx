"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

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

const FORM_SLUGS = new Set([
  "create-support-ticket",
  "ticket-assignment",
  "ticket-priority-management",
  "ticket-status-management",
  "escalation-management",
  "support-communication",
  "ticket-resolution",
  "helpdesk-settings",
]);

export function HelpdeskScreen({ slug, title }: { slug: string; title: string }) {
  const { apiPath, viewType } = resolveModuleEndpoint("helpdesk", slug);
  if (slug === "helpdesk-dashboard") {
    return <HelpdeskDashboard />;
  }
  if (slug === "all-support-tickets") {
    return (
      <GenericModuleScreen
        moduleKey="helpdesk"
        slug={slug}
        title={title}
        apiPath="/college-admin/helpdesk/tickets"
        viewType="list"
      />
    );
  }
  if (slug === "support-reports") {
    return (
      <GenericModuleScreen
        moduleKey="helpdesk"
        slug={slug}
        title={title}
        apiPath="/college-admin/helpdesk/reports/performance"
        viewType="report"
      />
    );
  }
  if (slug === "ticket-details") {
    return <TicketDetail title={title} />;
  }
  if (FORM_SLUGS.has(slug)) {
    return (
      <FormPlaceholder title={title} description="Helpdesk workflow (Figma CA 21)." />
    );
  }
  return (
    <GenericModuleScreen
      moduleKey="helpdesk"
      slug={slug}
      title={title}
      apiPath={apiPath}
      viewType={viewType}
    />
  );
}

function HelpdeskDashboard() {
  const perf = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "helpdesk-perf"],
    queryFn: () =>
      apiRequest<Record<string, unknown>>("/college-admin/helpdesk/reports/performance"),
  });
  const tickets = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "helpdesk-tickets"],
    queryFn: () =>
      apiRequest<{ items?: unknown[]; total?: number }>(
        "/college-admin/helpdesk/tickets?limit=25&offset=0",
      ),
  });
  const cats = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "helpdesk-cats"],
    queryFn: () => apiRequest<unknown[]>("/college-admin/helpdesk/categories"),
  });
  const rows = rowsFromApi(tickets.data?.items);
  return (
    <QueryState
      isLoading={tickets.isLoading}
      isError={tickets.isError}
      error={tickets.error}
      onRetry={() => void tickets.refetch()}
    >
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Open tickets" value={String(perf.data?.open_tickets ?? tickets.data?.total ?? "—")} />
        <StatCard label="Categories" value={rowsFromApi(cats.data).length} />
        <Link href="/college-admin/helpdesk/all-support-tickets" className="text-sm font-medium text-[#245dd8]">
          All tickets →
        </Link>
        <Link href="/college-admin/helpdesk/create-support-ticket" className="text-sm font-medium text-[#245dd8]">
          Create ticket →
        </Link>
      </div>
      <SectionPanel title="Recent tickets" className="mt-6">
        <ToolbarRow onRefresh={() => void tickets.refetch()} />
        <DataTable columns={columnsFromRows(rows)} rows={rows} />
      </SectionPanel>
    </QueryState>
  );
}

function TicketDetail({ title }: { title: string }) {
  const params = useSearchParams();
  const id = params.get("id") ?? "";
  const q = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "ticket", id],
    queryFn: () =>
      apiRequest<Record<string, unknown>>(
        `/college-admin/helpdesk/tickets/${encodeURIComponent(id)}`,
      ),
    enabled: Boolean(id),
  });
  if (!id) {
    return (
      <SectionPanel title={title}>
        <Link href="/college-admin/helpdesk/all-support-tickets" className="text-sm text-[#245dd8]">
          Select a ticket from the list
        </Link>
      </SectionPanel>
    );
  }
  return (
    <QueryState isLoading={q.isLoading} isError={q.isError} error={q.error} onRetry={() => void q.refetch()}>
      <SectionPanel title={title}>
        <DetailGrid record={q.data ?? {}} />
      </SectionPanel>
    </QueryState>
  );
}