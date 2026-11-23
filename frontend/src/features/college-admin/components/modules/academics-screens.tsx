"use client";

import { AcademicConfigurationDashboard } from "@/features/college-admin/components/academics/academic-configuration-dashboard";
import { AcademicConfigurationHistoryDashboard } from "@/features/college-admin/components/academics/academic-configuration-history-dashboard";
import { AcademicYearDetailsDashboard } from "@/features/college-admin/components/academics/academic-year-details-dashboard";
import { AcademicYearManagementDashboard } from "@/features/college-admin/components/academics/academic-year-management-dashboard";
import { CreateAcademicYearDashboard } from "@/features/college-admin/components/academics/create-academic-year-dashboard";
import { CourseConfigurationDashboard } from "@/features/college-admin/components/academics/course-configuration-dashboard";
import { CreditConfigurationDashboard } from "@/features/college-admin/components/academics/credit-configuration-dashboard";
import { GradingSystemConfigurationDashboard } from "@/features/college-admin/components/academics/grading-system-configuration-dashboard";
import { CurriculumManagementDashboard } from "@/features/college-admin/components/academics/curriculum-management-dashboard";
import { CreateProgrammeDashboard } from "@/features/college-admin/components/academics/create-programme-dashboard";
import { ProgrammeDetailsDashboard } from "@/features/college-admin/components/academics/programme-details-dashboard";
import { ProgrammeManagementDashboard } from "@/features/college-admin/components/academics/programme-management-dashboard";
import { AcademicCalendarConfigurationDashboard } from "@/features/college-admin/components/academics/academic-calendar-configuration-dashboard";
import { CreateCalendarEventDashboard } from "@/features/college-admin/components/academics/create-calendar-event-dashboard";
import { CreateSemesterDashboard } from "@/features/college-admin/components/academics/create-semester-dashboard";
import { SemesterDetailsDashboard } from "@/features/college-admin/components/academics/semester-details-dashboard";
import { BatchSectionConfigurationDashboard } from "@/features/college-admin/components/academics/batch-section-configuration-dashboard";
import { RegulationManagementDashboard } from "@/features/college-admin/components/academics/regulation-management-dashboard";
import { SemesterManagementDashboard } from "@/features/college-admin/components/academics/semester-management-dashboard";
import { SubjectManagementDashboard } from "@/features/college-admin/components/academics/subject-management-dashboard";
export function AcademicsScreen({ slug }: { slug: string }) {
  switch (slug) {
    case "academic-configuration-dashboard":
      return <AcademicConfigurationDashboard />;
    case "academic-year-management":
      return <AcademicYearManagementDashboard />;
    case "create-academic-year":
      return <CreateAcademicYearDashboard />;
    case "academic-year-details":
      return <AcademicYearDetailsDashboard />;
    case "semester-management":
      return <SemesterManagementDashboard />;
    case "create-semester":
      return <CreateSemesterDashboard />;
    case "semester-details":
      return <SemesterDetailsDashboard />;
    case "create-calendar-event":
      return <CreateCalendarEventDashboard />;
    case "programme-management":
      return <ProgrammeManagementDashboard />;
    case "create-programme":
      return <CreateProgrammeDashboard />;
    case "programme-details":
      return <ProgrammeDetailsDashboard />;
    case "academic-configuration-history":
      return <AcademicConfigurationHistoryDashboard />;
    case "course-configuration":
      return <CourseConfigurationDashboard />;
    case "curriculum-management":
      return <CurriculumManagementDashboard />;
    case "subject-management":
      return <SubjectManagementDashboard />;
    case "credit-configuration":
      return <CreditConfigurationDashboard />;
    case "grading-system-configuration":
      return <GradingSystemConfigurationDashboard />;
    case "regulation-management":
      return <RegulationManagementDashboard />;
    case "academic-calendar-configuration":
      return <AcademicCalendarConfigurationDashboard />;
    case "batch-section-configuration":
      return <BatchSectionConfigurationDashboard />;
    default:
      return <AcademicConfigurationDashboard />;
  }
}