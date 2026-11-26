"use client";

import { EmployeeAttendanceDashboard } from "@/features/college-admin/components/hr/employee-attendance-dashboard";
import { EmployeeManagementDashboard } from "@/features/college-admin/components/hr/employee-management-dashboard";
import { EmployeeOnboardingDashboard } from "@/features/college-admin/components/hr/employee-onboarding-dashboard";
import { HrDashboard } from "@/features/college-admin/components/hr/hr-dashboard";
import { LeaveApprovalDashboard } from "@/features/college-admin/components/hr/leave-approval-dashboard";
import { LeaveManagementDashboard } from "@/features/college-admin/components/hr/leave-management-dashboard";
import { EmployeeBenefitsClaimsDashboard } from "@/features/college-admin/components/hr/employee-benefits-claims-dashboard";
import { PerformanceManagementDashboard } from "@/features/college-admin/components/hr/performance-management-dashboard";
import { HrReportsDashboard } from "@/features/college-admin/components/hr/hr-reports-dashboard";
import { HrSettingsPoliciesDashboard } from "@/features/college-admin/components/hr/hr-settings-policies-dashboard";
import { PayrollProcessingDashboard } from "@/features/college-admin/components/hr/payroll-processing-dashboard";
import { RecruitmentManagementDashboard } from "@/features/college-admin/components/hr/recruitment-management-dashboard";
import { SalarySlipManagementDashboard } from "@/features/college-admin/components/hr/salary-slip-management-dashboard";
import { SalaryStructureManagementDashboard } from "@/features/college-admin/components/hr/salary-structure-management-dashboard";
import { GenericModuleScreen } from "@/features/college-admin/components/modules/generic-module-screen";
import { resolveModuleEndpoint } from "@/features/college-admin/config/module-endpoint-resolver";

export function HrScreen({ slug, title }: { slug: string; title: string }) {
  const { apiPath, viewType } = resolveModuleEndpoint("hr", slug);
  if (slug === "hr-dashboard") {
    return <HrDashboard />;
  }
  if (slug === "employee-management") {
    return <EmployeeManagementDashboard />;
  }
  if (slug === "recruitment-management") {
    return <RecruitmentManagementDashboard />;
  }
  if (slug === "employee-onboarding") {
    return <EmployeeOnboardingDashboard />;
  }
  if (slug === "employee-attendance") {
    return <EmployeeAttendanceDashboard />;
  }
  if (slug === "leave-management") {
    return <LeaveManagementDashboard />;
  }
  if (slug === "leave-approval") {
    return <LeaveApprovalDashboard />;
  }
  if (slug === "salary-structure-management") {
    return <SalaryStructureManagementDashboard />;
  }
  if (slug === "payroll-processing") {
    return <PayrollProcessingDashboard />;
  }
  if (slug === "salary-slip-management") {
    return <SalarySlipManagementDashboard />;
  }
  if (slug === "employee-benefits-claims") {
    return <EmployeeBenefitsClaimsDashboard />;
  }
  if (slug === "performance-management") {
    return <PerformanceManagementDashboard />;
  }
  if (slug === "hr-reports") {
    return <HrReportsDashboard />;
  }
  if (slug === "hr-settings-policies") {
    return <HrSettingsPoliciesDashboard />;
  }
  return (
    <GenericModuleScreen
      moduleKey="hr"
      slug={slug}
      title={title}
      apiPath={apiPath}
      viewType={viewType}
    />
  );
}