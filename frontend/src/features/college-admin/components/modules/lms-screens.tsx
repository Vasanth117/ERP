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
  "course-management",
  "subject-course-mapping",
  "learning-material-management",
  "video-lecture-management",
  "unit-chapter-management",
  "assignment-management",
  "quiz-management",
  "assessment-management",
  "student-learning-progress",
  "faculty-content-management",
  "lms-settings",
]);

export function LmsScreen({ slug, title }: { slug: string; title: string }) {
  const { apiPath, viewType } = resolveModuleEndpoint("lms", slug);
  if (slug === "lms-dashboard") {
    return <LmsDashboard />;
  }
  if (slug === "lms-reports") {
    return (
      <GenericModuleScreen
        moduleKey="lms"
        slug={slug}
        title={title}
        apiPath="/college-admin/lms-administration/monitoring"
        viewType="report"
      />
    );
  }
  if (FORM_SLUGS.has(slug)) {
    return <FormPlaceholder title={title} description="LMS administration workflow (Figma CA 15)." />;
  }
  return (
    <GenericModuleScreen
      moduleKey="lms"
      slug={slug}
      title={title}
      apiPath={apiPath}
      viewType={viewType}
    />
  );
}

function LmsDashboard() {
  const stats = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "lms-stats"],
    queryFn: () =>
      apiRequest<Record<string, unknown>>("/college-admin/lms-administration/statistics"),
  });
  const mappings = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "lms-mappings"],
    queryFn: () =>
      apiRequest<unknown[]>("/college-admin/lms-administration/course-mappings"),
  });
  const rows = rowsFromApi(mappings.data);
  return (
    <QueryState
      isLoading={stats.isLoading}
      isError={stats.isError}
      error={stats.error}
      onRetry={() => void stats.refetch()}
    >
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Active courses" value={String(stats.data?.active_courses ?? "—")} />
        <StatCard label="Course mappings" value={rows.length} />
        <Link
          href="/college-admin/lms/course-management"
          className="text-sm font-medium text-[#245dd8]"
        >
          Course management →
        </Link>
        <Link href="/college-admin/lms/lms-settings" className="text-sm font-medium text-[#245dd8]">
          LMS settings →
        </Link>
      </div>
      <SectionPanel title="Course mappings" className="mt-6">
        <ToolbarRow onRefresh={() => void mappings.refetch()} />
        <DataTable columns={columnsFromRows(rows)} rows={rows} />
      </SectionPanel>
    </QueryState>
  );
}