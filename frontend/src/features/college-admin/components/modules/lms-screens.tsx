"use client";

import { LmsDashboard } from "@/features/college-admin/components/lms/lms-dashboard";
import { LmsCourseManagementDashboard } from "@/features/college-admin/components/lms/lms-course-management-dashboard";
import { LmsSubjectCourseMappingDashboard } from "@/features/college-admin/components/lms/lms-subject-course-mapping-dashboard";
import { LmsLearningMaterialManagementDashboard } from "@/features/college-admin/components/lms/lms-learning-material-management-dashboard";
import { LmsVideoLectureManagementDashboard } from "@/features/college-admin/components/lms/lms-video-lecture-management-dashboard";
import { LmsAssignmentManagementDashboard } from "@/features/college-admin/components/lms/lms-assignment-management-dashboard";
import { LmsQuizManagementDashboard } from "@/features/college-admin/components/lms/lms-quiz-management-dashboard";
import { LmsAssessmentManagementDashboard } from "@/features/college-admin/components/lms/lms-assessment-management-dashboard";
import { LmsStudentLearningProgressDashboard } from "@/features/college-admin/components/lms/lms-student-learning-progress-dashboard";
import { LmsFacultyContentManagementDashboard } from "@/features/college-admin/components/lms/lms-faculty-content-management-dashboard";
import { LmsReportsDashboard } from "@/features/college-admin/components/lms/lms-reports-dashboard";
import { LmsSettingsDashboard } from "@/features/college-admin/components/lms/lms-settings-dashboard";
import { FormPlaceholder } from "@/features/college-admin/components/ui/college-admin-screen-ui";
import { GenericModuleScreen } from "@/features/college-admin/components/modules/generic-module-screen";
import { resolveModuleEndpoint } from "@/features/college-admin/config/module-endpoint-resolver";

const FORM_SLUGS = new Set(["unit-chapter-management"]);

export function LmsScreen({ slug, title }: { slug: string; title: string }) {
  const { apiPath, viewType } = resolveModuleEndpoint("lms", slug);
  if (slug === "lms-dashboard") {
    return <LmsDashboard />;
  }
  if (slug === "course-management") {
    return <LmsCourseManagementDashboard />;
  }
  if (slug === "subject-course-mapping") {
    return <LmsSubjectCourseMappingDashboard />;
  }
  if (slug === "learning-material-management") {
    return <LmsLearningMaterialManagementDashboard />;
  }
  if (slug === "video-lecture-management") {
    return <LmsVideoLectureManagementDashboard />;
  }
  if (slug === "assignment-management") {
    return <LmsAssignmentManagementDashboard />;
  }
  if (slug === "quiz-management") {
    return <LmsQuizManagementDashboard />;
  }
  if (slug === "assessment-management") {
    return <LmsAssessmentManagementDashboard />;
  }
  if (slug === "student-learning-progress") {
    return <LmsStudentLearningProgressDashboard />;
  }
  if (slug === "faculty-content-management") {
    return <LmsFacultyContentManagementDashboard />;
  }
  if (slug === "lms-reports") {
    return <LmsReportsDashboard />;
  }
  if (slug === "lms-settings") {
    return <LmsSettingsDashboard />;
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