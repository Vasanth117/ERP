"use client";

import { FormPlaceholder } from "@/features/college-admin/components/ui/college-admin-screen-ui";
import { GenericModuleScreen } from "@/features/college-admin/components/modules/generic-module-screen";
import { ExaminationConfigurationDashboard } from "@/features/college-admin/components/examinations/examination-configuration-dashboard";
import { ExaminationDashboard } from "@/features/college-admin/components/examinations/examination-dashboard";
import { ExaminationSessionManagementDashboard } from "@/features/college-admin/components/examinations/examination-session-management-dashboard";
import { ExamRegistrationManagementDashboard } from "@/features/college-admin/components/examinations/exam-registration-management-dashboard";
import { ExamTimetableManagementDashboard } from "@/features/college-admin/components/examinations/exam-timetable-management-dashboard";
import { ExaminationHallSeatingManagementDashboard } from "@/features/college-admin/components/examinations/examination-hall-seating-management-dashboard";
import { HallTicketAdministrationDashboard } from "@/features/college-admin/components/examinations/hall-ticket-administration-dashboard";
import { InternalExternalAssessmentDashboard } from "@/features/college-admin/components/examinations/internal-external-assessment-dashboard";
import { InvigilatorAllocationDashboard } from "@/features/college-admin/components/examinations/invigilator-allocation-dashboard";
import { MarksEntryManagementDashboard } from "@/features/college-admin/components/examinations/marks-entry-management-dashboard";
import { ResultApprovalDashboard } from "@/features/college-admin/components/examinations/result-approval-dashboard";
import { ResultProcessingDashboard } from "@/features/college-admin/components/examinations/result-processing-dashboard";
import { ResultPublicationDashboard } from "@/features/college-admin/components/examinations/result-publication-dashboard";
import { RevaluationManagementDashboard } from "@/features/college-admin/components/examinations/revaluation-management-dashboard";
import { SupplementaryExaminationManagementDashboard } from "@/features/college-admin/components/examinations/supplementary-examination-management-dashboard";
import { StudentExamEligibilityDashboard } from "@/features/college-admin/components/examinations/student-exam-eligibility-dashboard";
import { resolveModuleEndpoint } from "@/features/college-admin/config/module-endpoint-resolver";

const FORM_SLUGS = new Set<string>([]);

export function ExaminationsScreen({ slug, title }: { slug: string; title: string }) {
  const { apiPath, viewType } = resolveModuleEndpoint("examinations", slug);
  if (slug === "examination-dashboard") {
    return <ExaminationDashboard />;
  }
  if (slug === "exam-registration-management") {
    return <ExamRegistrationManagementDashboard />;
  }
  if (slug === "examination-session-management") {
    return <ExaminationSessionManagementDashboard />;
  }
  if (slug === "examination-configuration") {
    return <ExaminationConfigurationDashboard />;
  }
  if (slug === "exam-timetable-management") {
    return <ExamTimetableManagementDashboard />;
  }
  if (slug === "student-exam-eligibility") {
    return <StudentExamEligibilityDashboard />;
  }
  if (slug === "hall-ticket-administration") {
    return <HallTicketAdministrationDashboard />;
  }
  if (slug === "examination-hall-seating-management") {
    return <ExaminationHallSeatingManagementDashboard />;
  }
  if (slug === "invigilator-allocation") {
    return <InvigilatorAllocationDashboard />;
  }
  if (slug === "marks-entry-management") {
    return <MarksEntryManagementDashboard />;
  }
  if (slug === "internal-external-assessment") {
    return <InternalExternalAssessmentDashboard />;
  }
  if (slug === "result-processing") {
    return <ResultProcessingDashboard />;
  }
  if (slug === "result-approval") {
    return <ResultApprovalDashboard />;
  }
  if (slug === "result-publication") {
    return <ResultPublicationDashboard />;
  }
  if (slug === "revaluation-management") {
    return <RevaluationManagementDashboard />;
  }
  if (slug === "supplementary-examination-management") {
    return <SupplementaryExaminationManagementDashboard />;
  }
  if (FORM_SLUGS.has(slug)) {
    return (
      <FormPlaceholder title={title} description="Examination administration workflow (Figma CA 09)." />
    );
  }
  return (
    <GenericModuleScreen
      moduleKey="examinations"
      slug={slug}
      title={title}
      apiPath={apiPath}
      viewType={viewType}
    />
  );
}