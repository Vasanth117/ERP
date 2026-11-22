"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { fetchFaculty, fetchFacultyHistory } from "@/features/college-admin/api/faculty";
import { AddNewFacultyEmployeeDashboard } from "@/features/college-admin/components/faculty/add-new-faculty-employee-dashboard";
import { DepartmentDesignationAssignmentDashboard } from "@/features/college-admin/components/faculty/department-designation-assignment-dashboard";
import { FacultySubjectAllocationDashboard } from "@/features/college-admin/components/faculty/faculty-subject-allocation-dashboard";
import { FacultyTimetableDashboard } from "@/features/college-admin/components/faculty/faculty-timetable-dashboard";
import { FacultyWorkloadManagementDashboard } from "@/features/college-admin/components/faculty/faculty-workload-management-dashboard";
import { EmployeeDocumentVerificationDashboard } from "@/features/college-admin/components/faculty/employee-document-verification-dashboard";
import { EmployeeStatusManagementDashboard } from "@/features/college-admin/components/faculty/employee-status-management-dashboard";
import { FacultyEmployeeHistoryDashboard } from "@/features/college-admin/components/faculty/faculty-employee-history-dashboard";
import { EmployeeDirectoryDashboard } from "@/features/college-admin/components/faculty/employee-directory-dashboard";
import { EmployeeProfileManagementDashboard } from "@/features/college-admin/components/faculty/employee-profile-management-dashboard";
import { FacultyDirectoryDashboard } from "@/features/college-admin/components/faculty/faculty-directory-dashboard";
import { FacultyEmployeeDashboard } from "@/features/college-admin/components/faculty/faculty-employee-dashboard";
import { FacultyProfileDashboard } from "@/features/college-admin/components/faculty/faculty-profile-dashboard";
import {
  DetailGrid,
  FormPlaceholder,
  SectionPanel,
  rowsFromApi,
} from "@/features/college-admin/components/ui/college-admin-screen-ui";
import { GenericModuleScreen } from "@/features/college-admin/components/modules/generic-module-screen";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { resolveModuleEndpoint } from "@/features/college-admin/config/module-endpoint-resolver";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function FacultyScreen({ slug, title }: { slug: string; title: string }) {
  const { apiPath, viewType } = resolveModuleEndpoint("faculty", slug);

  if (slug === "faculty-employee-dashboard") {
    return <FacultyEmployeeDashboard />;
  }
  if (slug === "faculty-directory" || slug === "all-faculty-list") {
    return <FacultyDirectoryDashboard />;
  }
  if (slug === "employee-directory") {
    return <EmployeeDirectoryDashboard />;
  }
  if (slug === "faculty-profile" || slug === "faculty-details") {
    return <FacultyProfileDashboard />;
  }
  if (slug === "add-new-faculty-employee") {
    return <AddNewFacultyEmployeeDashboard />;
  }
  if (slug === "employee-profile-management") {
    return <EmployeeProfileManagementDashboard />;
  }
  if (slug === "department-designation-assignment") {
    return <DepartmentDesignationAssignmentDashboard />;
  }
  if (slug === "faculty-subject-allocation") {
    return <FacultySubjectAllocationDashboard />;
  }
  if (slug === "faculty-workload-management") {
    return <FacultyWorkloadManagementDashboard />;
  }
  if (slug === "faculty-timetable") {
    return <FacultyTimetableDashboard />;
  }
  if (slug === "employee-document-verification") {
    return <EmployeeDocumentVerificationDashboard />;
  }
  if (slug === "employee-status-management") {
    return <EmployeeStatusManagementDashboard />;
  }
  if (slug === "faculty-employee-history") {
    return <FacultyEmployeeHistoryDashboard />;
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