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
  "library-branch-management",
  "book-catalogue",
  "book-inventory",
  "book-acquisition",
  "book-issue-return-management",
  "reservation-management",
  "library-member-management",
  "fine-management",
  "lost-damaged-books",
  "digital-library-management",
  "library-settings",
]);

export function LibraryScreen({ slug, title }: { slug: string; title: string }) {
  const { apiPath, viewType } = resolveModuleEndpoint("library", slug);
  if (slug === "library-dashboard") {
    return <LibraryDashboard />;
  }
  if (slug === "library-reports") {
    return (
      <GenericModuleScreen
        moduleKey="library"
        slug={slug}
        title={title}
        apiPath="/college-admin/library-administration/reports/summary"
        viewType="report"
      />
    );
  }
  if (FORM_SLUGS.has(slug)) {
    return (
      <FormPlaceholder title={title} description="Library administration workflow (Figma CA 12)." />
    );
  }
  return (
    <GenericModuleScreen
      moduleKey="library"
      slug={slug}
      title={title}
      apiPath={apiPath}
      viewType={viewType}
    />
  );
}

function LibraryDashboard() {
  const summary = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "library-summary"],
    queryFn: () =>
      apiRequest<Record<string, unknown>>("/college-admin/library-administration/reports/summary"),
  });
  const circulation = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "library-circulation"],
    queryFn: () =>
      apiRequest<{ items?: unknown[]; total?: number }>(
        "/college-admin/library-administration/circulation?limit=25&offset=0",
      ),
  });
  const rows = rowsFromApi(circulation.data?.items);
  return (
    <QueryState
      isLoading={summary.isLoading}
      isError={summary.isError}
      error={summary.error}
      onRetry={() => void summary.refetch()}
    >
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Catalog items" value={String(summary.data?.catalog_items ?? "—")} />
        <StatCard label="Active loans" value={circulation.data?.total ?? rows.length} />
        <Link
          href="/college-admin/library/book-issue-return-management"
          className="text-sm font-medium text-[#245dd8]"
        >
          Issue / return →
        </Link>
        <Link href="/college-admin/library/library-reports" className="text-sm font-medium text-[#245dd8]">
          Reports →
        </Link>
      </div>
      <SectionPanel title="Circulation" className="mt-6">
        <ToolbarRow onRefresh={() => void circulation.refetch()} />
        <DataTable columns={columnsFromRows(rows)} rows={rows} />
      </SectionPanel>
    </QueryState>
  );
}