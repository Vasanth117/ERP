"use client";

import { AttendanceDashboardDashboard } from "@/features/college-admin/components/attendance/attendance-dashboard-dashboard";
import { AttendanceApprovalDashboard } from "@/features/college-admin/components/attendance/attendance-approval-dashboard";
import { AttendanceConfigurationDashboard } from "@/features/college-admin/components/attendance/attendance-configuration-dashboard";
import { AttendanceCorrectionRequestsDashboard } from "@/features/college-admin/components/attendance/attendance-correction-requests-dashboard";
import { AttendanceMonitoringDashboard } from "@/features/college-admin/components/attendance/attendance-monitoring-dashboard";
import { AttendanceReportsDashboard } from "@/features/college-admin/components/attendance/attendance-reports-dashboard";
import { AttendanceRulesPoliciesDashboard } from "@/features/college-admin/components/attendance/attendance-rules-policies-dashboard";
import { DepartmentWiseAttendanceDashboard } from "@/features/college-admin/components/attendance/department-wise-attendance-dashboard";
import { FacultyAttendanceOverviewDashboard } from "@/features/college-admin/components/attendance/faculty-attendance-overview-dashboard";
import { StudentAttendanceOverviewDashboard } from "@/features/college-admin/components/attendance/student-attendance-overview-dashboard";
import { SubjectWiseAttendanceDashboard } from "@/features/college-admin/components/attendance/subject-wise-attendance-dashboard";
import { GenericModuleScreen } from "@/features/college-admin/components/modules/generic-module-screen";
import { resolveModuleEndpoint } from "@/features/college-admin/config/module-endpoint-resolver";

export function AttendanceScreen({ slug, title }: { slug: string; title: string }) {
  const { apiPath, viewType } = resolveModuleEndpoint("attendance", slug);
  if (slug === "attendance-dashboard") {
    return <AttendanceDashboardDashboard />;
  }
  if (slug === "student-attendance-overview") {
    return <StudentAttendanceOverviewDashboard />;
  }
  if (slug === "faculty-attendance-overview") {
    return <FacultyAttendanceOverviewDashboard />;
  }
  if (slug === "department-wise-attendance") {
    return <DepartmentWiseAttendanceDashboard />;
  }
  if (slug === "subject-wise-attendance") {
    return <SubjectWiseAttendanceDashboard />;
  }
  if (slug === "attendance-monitoring") {
    return <AttendanceMonitoringDashboard />;
  }
  if (slug === "attendance-correction-requests" || slug === "correction-requests") {
    return <AttendanceCorrectionRequestsDashboard />;
  }
  if (slug === "attendance-approval") {
    return <AttendanceApprovalDashboard />;
  }
  if (slug === "attendance-configuration") {
    return <AttendanceConfigurationDashboard />;
  }
  if (slug === "attendance-rules-policies" || slug === "attendance-policies") {
    return <AttendanceRulesPoliciesDashboard />;
  }
  if (slug === "attendance-reports" || slug === "compliance-reports") {
    return <AttendanceReportsDashboard />;
  }
  return (
    <GenericModuleScreen
      moduleKey="attendance"
      slug={slug}
      title={title}
      apiPath={apiPath}
      viewType={viewType}
    />
  );
}