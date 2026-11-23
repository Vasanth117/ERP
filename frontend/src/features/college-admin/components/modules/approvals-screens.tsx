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

const FORM_SLUGS = new Set([
  "approval-workflow-configuration",
  "create-approval-workflow",
  "approval-level-management",
  "approver-assignment",
  "approval-rules-conditions",
  "escalation-management",
]);

export function ApprovalsScreen({ slug, title }: { slug: string; title: string }) {
  const { apiPath, viewType } = resolveModuleEndpoint("approvals", slug);
  if (slug === "approval-dashboard") {
    return <ApprovalsDashboard />;
  }
  if (slug === "pending-approval-requests") {
    return (
      <GenericModuleScreen
        moduleKey="approvals"
        slug={slug}
        title={title}
        apiPath="/college-admin/workflow-administration/pending"
        viewType="list"
      />
    );
  }
  if (slug === "approval-history") {
    return <ApprovalHistory title={title} />;
  }
  if (slug === "approval-request-details") {
    return <ApprovalDetail title={title} />;
  }
  if (slug === "escalation-management") {
    return (
      <GenericModuleScreen
        moduleKey="approvals"
        slug={slug}
        title={title}
        apiPath="/college-admin/workflow-administration/escalations"
        viewType="list"
      />
    );
  }
  if (slug === "approved-requests" || slug === "rejected-requests") {
    return (
      <GenericModuleScreen
        moduleKey="approvals"
        slug={slug}
        title={title}
        apiPath="/college-admin/workflow-administration/pending"
        viewType="list"
      />
    );
  }
  if (FORM_SLUGS.has(slug)) {
    return (
      <FormPlaceholder title={title} description="Workflow & approval configuration (Figma CA 17)." />
    );
  }
  return (
    <GenericModuleScreen
      moduleKey="approvals"
      slug={slug}
      title={title}
      apiPath={apiPath}
      viewType={viewType}
    />
  );
}

function ApprovalsDashboard() {
  const pending = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "approvals-pending"],
    queryFn: () =>
      apiRequest<{ total?: number; items?: unknown[] }>(
        "/college-admin/workflow-administration/pending?limit=25&offset=0",
      ),
  });
  const defs = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "workflow-defs"],
    queryFn: () =>
      apiRequest<unknown[]>("/college-admin/workflow-administration/definitions"),
  });
  const rows = rowsFromApi(pending.data?.items);
  const defRows = rowsFromApi(defs.data);
  return (
    <QueryState
      isLoading={pending.isLoading}
      isError={pending.isError}
      error={pending.error}
      onRetry={() => void pending.refetch()}
    >
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Pending approvals" value={pending.data?.total ?? rows.length} />
        <StatCard label="Workflow definitions" value={defRows.length} />
        <Link
          href="/college-admin/approvals/pending-approval-requests"
          className="text-sm font-medium text-[#245dd8]"
        >
          Pending requests →
        </Link>
        <Link
          href="/college-admin/approvals/approval-workflow-configuration"
          className="text-sm font-medium text-[#245dd8]"
        >
          Configure workflows →
        </Link>
      </div>
      <SectionPanel title="Pending tasks" className="mt-6">
        <ToolbarRow onRefresh={() => void pending.refetch()} />
        <DataTable columns={columnsFromRows(rows)} rows={rows} />
      </SectionPanel>
    </QueryState>
  );
}

function ApprovalDetail({ title }: { title: string }) {
  const params = useSearchParams();
  const id = params.get("id") ?? "";
  if (!id) {
    return (
      <SectionPanel title={title}>
        <p className="text-sm text-[#607086]">
          Open from{" "}
          <Link href="/college-admin/approvals/pending-approval-requests" className="text-[#245dd8]">
            pending requests
          </Link>{" "}
          with <code>?id=</code> instance id.
        </p>
      </SectionPanel>
    );
  }
  const q = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "approval-history", id],
    queryFn: () =>
      apiRequest<unknown[]>(
        `/college-admin/workflow-administration/instances/${encodeURIComponent(id)}/history`,
      ),
    enabled: Boolean(id),
  });
  const rows = rowsFromApi(q.data);
  return (
    <QueryState
      isLoading={q.isLoading}
      isError={q.isError}
      error={q.error}
      onRetry={() => void q.refetch()}
    >
      <SectionPanel title={title}>
        {rows[0] ? <DetailGrid record={rows[0]} /> : <DataTable columns={columnsFromRows(rows)} rows={rows} />}
      </SectionPanel>
    </QueryState>
  );
}

function ApprovalHistory({ title }: { title: string }) {
  return (
    <GenericModuleScreen
      moduleKey="approvals"
      slug="approval-history"
      title={title}
      apiPath="/college-admin/workflow-administration/definitions"
      viewType="list"
    />
  );
}