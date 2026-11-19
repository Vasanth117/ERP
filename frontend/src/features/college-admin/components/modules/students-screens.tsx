"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

import { apiRequest } from "@/lib/api/client";
import {
  fetchAdmissions,
  fetchStudent,
  fetchStudents,
} from "@/features/college-admin/api/students";
import {
  DataTable,
  DetailGrid,
  FormPlaceholder,
  SectionPanel,
  ToolbarRow,
  columnsFromRows,
  rowsFromApi,
} from "@/features/college-admin/components/ui/college-admin-screen-ui";
import {
  QueryState,
  StatCard,
} from "@/features/college-admin/components/ui/query-state";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function StudentsScreen({ slug }: { slug: string }) {
  switch (slug) {
    case "student-administration-dashboard":
      return <StudentsDashboard />;
    case "all-students-list":
      return <StudentsList />;
    case "admissions-list":
      return <AdmissionsList />;
    case "student-details":
    case "academic-history":
      return <StudentDetailPicker />;
    case "create-student":
    case "bulk-student-import":
    case "profile-corrections":
      return (
        <FormPlaceholder
          title={slug.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
          description="Student administration workflow matching the Figma form layout."
          submitLabel={slug.includes("bulk") ? "Start import" : "Submit"}
        />
      );
    case "section-transfer-review":
      return <SectionTransferList />;
    default:
      return <StudentsList />;
  }
}

function StudentsDashboard() {
  const q = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "students-dash"],
    queryFn: () => fetchStudents(10, 0),
  });
  return (
    <QueryState
      isLoading={q.isLoading}
      isError={q.isError}
      error={q.error}
      onRetry={() => void q.refetch()}
    >
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <StatCard label="Total students" value={q.data?.total ?? 0} />
        <StatCard label="On this page" value={q.data?.items?.length ?? 0} />
        <Link
          href="/college-admin/students/all-students-list"
          className="flex items-center text-sm font-medium text-[#245dd8]"
        >
          Open student registry →
        </Link>
      </div>
    </QueryState>
  );
}

function StudentsList() {
  const q = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "students-list"],
    queryFn: () => fetchStudents(100, 0),
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
      <SectionPanel title="All students">
        <ToolbarRow onRefresh={() => void q.refetch()} />
        <DataTable columns={cols.length ? cols : ["full_name", "email", "status"]} rows={rows} />
      </SectionPanel>
    </QueryState>
  );
}

function AdmissionsList() {
  const q = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "admissions-list"],
    queryFn: () => fetchAdmissions(100, 0),
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
      <SectionPanel title="Admissions">
        <ToolbarRow onRefresh={() => void q.refetch()} />
        <DataTable columns={cols} rows={rows} />
      </SectionPanel>
    </QueryState>
  );
}

function StudentDetailPicker() {
  const params = useSearchParams();
  const id = params.get("id") ?? "";
  const q = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "student", id],
    queryFn: () => fetchStudent(id),
    enabled: Boolean(id),
  });

  if (!id) {
    return (
      <SectionPanel title="Student details" description="Choose a record from the student list.">
        <p className="text-sm text-[#607086]">
          Open{" "}
          <Link href="/college-admin/students/all-students-list" className="text-[#245dd8]">
            All students
          </Link>{" "}
          and pass <code>?id=</code> with a record id, or select from the table when deep links are
          added.
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
      <SectionPanel title="Student record">
        <DetailGrid record={q.data as Record<string, unknown>} />
      </SectionPanel>
    </QueryState>
  );
}

function SectionTransferList() {
  const q = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "section-transfers"],
    queryFn: () =>
      apiRequest<unknown>("/college-admin/student-administration/section-transfer-requests"),
  });
  const rows = rowsFromApi(q.data);
  const cols = columnsFromRows(rows);
  return (
    <QueryState
      isLoading={q.isLoading}
      isError={q.isError}
      error={q.error}
      isEmpty={!rows.length}
      onRetry={() => void q.refetch()}
    >
      <SectionPanel title="Section transfer requests">
        <ToolbarRow onRefresh={() => void q.refetch()} />
        <DataTable columns={cols} rows={rows} />
      </SectionPanel>
    </QueryState>
  );
}