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
  "student-data-import",
  "faculty-data-import",
  "department-data-import",
  "bulk-data-upload",
  "file-mapping-field-configuration",
  "data-validation",
  "import-preview-confirmation",
  "data-export-management",
]);

export function DataImportScreen({ slug, title }: { slug: string; title: string }) {
  const { apiPath, viewType } = resolveModuleEndpoint("data-import", slug);
  if (slug === "data-management-dashboard" || slug === "data-import-dashboard") {
    return <DataImportDashboard />;
  }
  if (slug === "import-history" || slug === "migration-progress") {
    return (
      <GenericModuleScreen
        moduleKey="data-import"
        slug={slug}
        title={title}
        apiPath="/college-admin/data-import/migration-history"
        viewType="list"
      />
    );
  }
  if (slug === "import-error-details") {
    return (
      <GenericModuleScreen
        moduleKey="data-import"
        slug={slug}
        title={title}
        apiPath="/college-admin/data-import/error-reports/download"
        viewType="report"
      />
    );
  }
  if (FORM_SLUGS.has(slug)) {
    return (
      <FormPlaceholder title={title} description="Data import & migration wizard (Figma CA 19)." />
    );
  }
  return (
    <GenericModuleScreen
      moduleKey="data-import"
      slug={slug}
      title={title}
      apiPath={apiPath}
      viewType={viewType}
    />
  );
}

function DataImportDashboard() {
  const templates = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "import-templates"],
    queryFn: () => apiRequest<unknown[]>("/college-admin/data-import/templates"),
  });
  const history = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "import-history"],
    queryFn: () =>
      apiRequest<{ items?: unknown[]; total?: number }>(
        "/college-admin/data-import/migration-history?limit=25&offset=0",
      ),
  });
  const templateRows = rowsFromApi(templates.data);
  const histRows = rowsFromApi(history.data);
  return (
    <QueryState
      isLoading={templates.isLoading}
      isError={templates.isError}
      error={templates.error}
      onRetry={() => void templates.refetch()}
    >
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Import templates" value={templateRows.length} />
        <StatCard label="Migration runs" value={history.data?.total ?? histRows.length} />
        <Link href="/college-admin/data-import/bulk-data-upload" className="text-sm font-medium text-[#245dd8]">
          Bulk upload →
        </Link>
        <Link href="/college-admin/data-import/import-history" className="text-sm font-medium text-[#245dd8]">
          Import history →
        </Link>
      </div>
      <SectionPanel title="Templates" className="mt-6">
        <ToolbarRow onRefresh={() => void templates.refetch()} />
        <DataTable columns={columnsFromRows(templateRows)} rows={templateRows} />
      </SectionPanel>
    </QueryState>
  );
}