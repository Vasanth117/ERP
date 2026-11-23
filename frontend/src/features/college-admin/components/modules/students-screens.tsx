"use client";

import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { apiRequest } from "@/lib/api/client";
import { AllStudentsListDashboard } from "@/features/college-admin/components/students/all-students-list-dashboard";
import { StudentAdmissionDashboard } from "@/features/college-admin/components/students/student-admission-dashboard";
import { StudentAdministrationDashboard } from "@/features/college-admin/components/students/student-administration-dashboard";
import { NewStudentRegistrationDashboard } from "@/features/college-admin/components/students/new-student-registration-dashboard";
import { StudentDetailsDashboard } from "@/features/college-admin/components/students/student-details-dashboard";
import { StudentDocumentVerificationDashboard } from "@/features/college-admin/components/students/student-document-verification-dashboard";
import { BatchSectionAllocationDashboard } from "@/features/college-admin/components/students/batch-section-allocation-dashboard";
import { StudentPromotionManagementDashboard } from "@/features/college-admin/components/students/student-promotion-management-dashboard";
import { StudentStatusManagementDashboard } from "@/features/college-admin/components/students/student-status-management-dashboard";
import { StudentWithdrawalDiscontinuationDashboard } from "@/features/college-admin/components/students/student-withdrawal-discontinuation-dashboard";
import { StudentTransferCreateDashboard } from "@/features/college-admin/components/students/student-transfer-create-dashboard";
import { StudentTransferManagementDashboard } from "@/features/college-admin/components/students/student-transfer-management-dashboard";
import { StudentEnrollmentManagementDashboard } from "@/features/college-admin/components/students/student-enrollment-management-dashboard";
import { StudentProfileManagementDashboard } from "@/features/college-admin/components/students/student-profile-management-dashboard";
import { StudentIdCardManagementDashboard } from "@/features/college-admin/components/students/student-id-card-management-dashboard";
import { StudentAcademicHistoryDashboard } from "@/features/college-admin/components/students/student-academic-history-dashboard";
import {
  DataTable,
  FormPlaceholder,
  SectionPanel,
  ToolbarRow,
  columnsFromRows,
  rowsFromApi,
} from "@/features/college-admin/components/ui/college-admin-screen-ui";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

export function StudentsScreen({ slug }: { slug: string }) {
  switch (slug) {
    case "student-administration-dashboard":
      return <StudentsDashboard />;
    case "all-students-list":
      return <AllStudentsListDashboard />;
    case "student-admission":
    case "admissions-list":
      return <StudentAdmissionDashboard />;
    case "new-student-registration":
      return <NewStudentRegistrationDashboard />;
    case "student-profile-management":
      return <StudentProfileManagementDashboard />;
    case "student-document-verification":
      return <StudentDocumentVerificationDashboard />;
    case "student-enrollment-management":
      return <StudentEnrollmentManagementDashboard />;
    case "batch-section-allocation":
      return <BatchSectionAllocationDashboard />;
    case "student-transfer-management":
      return <StudentTransferManagementDashboard />;
    case "student-transfer-create":
      return <StudentTransferCreateDashboard />;
    case "student-promotion-management":
      return <StudentPromotionManagementDashboard />;
    case "student-status-management":
      return <StudentStatusManagementDashboard />;
    case "student-withdrawal-discontinuation":
      return <StudentWithdrawalDiscontinuationDashboard />;
    case "student-id-card-management":
      return <StudentIdCardManagementDashboard />;
    case "student-academic-history":
    case "academic-history":
      return <StudentAcademicHistoryDashboard />;
    case "student-details":
      return <StudentDetailsDashboard />;
    case "create-student":
      return <NewStudentRegistrationDashboard />;
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
      return <AllStudentsListDashboard />;
  }
}

function StudentsDashboard() {
  return <StudentAdministrationDashboard />;
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