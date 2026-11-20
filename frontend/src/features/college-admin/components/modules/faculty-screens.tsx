"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

import {
  fetchFaculty,
  fetchFacultyHistory,
  fetchFacultyList,
} from "@/features/college-admin/api/faculty";
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

export function FacultyScreen({ slug, title }: { slug: string; title: string }) {
  const { apiPath, viewType } = resolveModuleEndpoint("faculty", slug);

  if (slug === "faculty-employee-dashboard") {
    return <FacultyDashboard />;
  }
  if (slug === "faculty-directory" || slug === "employee-directory") {
    return <FacultyDirectory title={title} />;
  }
  if (slug === "faculty-profile" || slug === "employee-profile-management") {
    return <FacultyProfile title={title} />;
  }
  if (slug === "faculty-employee-history") {
    return <FacultyHistory title={title} />;
  }
  if (
    [
      "add-new-faculty-employee",
      "department-designation-assignment",
      "faculty-subject-allocation",
      "faculty-workload-management",
      "faculty-timetable",
      "employee-document-verification",
      "employee-status-management",
    ].includes(slug)
  ) {
    return (
      <FormPlaceholder
        title={title}
        description="Faculty & employee workflow form aligned with Figma CA 07."
        submitLabel="Save"
      />
    );
  }

  return (
    <GenericModuleScreen
      moduleKey="faculty"
      slug={slug}
      title={title}
      apiPath={apiPath}
      viewType={viewType}
    />
  );
}

function FacultyDashboard() {
  const q = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "faculty-dashboard"],
    queryFn: () => fetchFacultyList(100, 0),
  });
  const active =
    q.data?.items.filter((f) => f.employment_status === "active").length ?? 0;
  return (
    <QueryState
      isLoading={q.isLoading}
      isError={q.isError}
      error={q.error}
      onRetry={() => void q.refetch()}
    >
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Total faculty & staff" value={q.data?.total ?? 0} />
        <StatCard label="Active" value={active} />
        <StatCard label="Listed" value={q.data?.items.length ?? 0} />
        <Link
          href="/college-admin/faculty/faculty-directory"
          className="flex items-center rounded-xl border border-[#dce3ec] bg-white p-4 text-sm font-medium text-[#245dd8]"
        >
          Open faculty directory →
        </Link>
      </div>
    </QueryState>
  );
}

function FacultyDirectory({ title }: { title: string }) {
  const q = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "faculty-list"],
    queryFn: () => fetchFacultyList(200, 0),
  });
  const rows = rowsFromApi(q.data?.items);
  const cols = columnsFromRows(rows);
  return (
    <QueryState
      isLoading={q.isLoading}
      isError={q.isError}
      error={q.error}
      isEmpty={!rows.length}
      onRetry={() => void q.refetch()}
    >
      <SectionPanel title={title}>
        <ToolbarRow onRefresh={() => void q.refetch()} />
        <DataTable columns={cols.length ? cols : ["full_name", "email", "designation", "employment_status"]} rows={rows} />
        {rows[0]?.record_id ? (
          <p className="mt-4 text-xs text-[#607086]">
            Open profile:{" "}
            <Link
              className="text-[#245dd8]"
              href={`/college-admin/faculty/faculty-profile?id=${encodeURIComponent(String(rows[0].record_id))}`}
            >
              sample record
            </Link>
          </p>
        ) : null}
      </SectionPanel>
    </QueryState>
  );
}

function FacultyProfile({ title }: { title: string }) {
  const params = useSearchParams();
  const id = params.get("id") ?? "";
  const q = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "faculty", id],
    queryFn: () => fetchFaculty(id),
    enabled: Boolean(id),
  });
  if (!id) {
    return (
      <SectionPanel title={title} description="Select a faculty member from the directory.">
        <Link href="/college-admin/faculty/faculty-directory" className="text-sm text-[#245dd8]">
          Go to faculty directory
        </Link>
      </SectionPanel>
    );
  }
  return (
    <QueryState
      isLoading={q.isLoading}
      isError={q.isError}
      error={q.error}
      onRetry={() => void q.refetch()}
    >
      <SectionPanel title={title}>
        <DetailGrid record={(q.data ?? {}) as Record<string, unknown>} />
      </SectionPanel>
    </QueryState>
  );
}

function FacultyHistory({ title }: { title: string }) {
  const params = useSearchParams();
  const id = params.get("id") ?? "";
  const q = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "faculty-history", id],
    queryFn: () => fetchFacultyHistory(id),
    enabled: Boolean(id),
  });
  if (!id) {
    return (
      <SectionPanel title={title}>
        <p className="text-sm text-[#607086]">
          Add <code>?id=</code> with a faculty <code>record_id</code>.
        </p>
      </SectionPanel>
    );
  }
  return (
    <QueryState
      isLoading={q.isLoading}
      isError={q.isError}
      error={q.error}
      onRetry={() => void q.refetch()}
    >
      <SectionPanel title={title}>
        <DetailGrid record={rowsFromApi(q.data)[0] ?? (q.data as Record<string, unknown>) ?? {}} />
      </SectionPanel>
    </QueryState>
  );
}