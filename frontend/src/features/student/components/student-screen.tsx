"use client";

import { AcademicsScreen } from "@/features/student/components/screens/academics-screens";
import { StudentDashboardScreen } from "@/features/student/components/screens/dashboard-screen";
import {
  StudentProfileAcademicScreen,
  StudentProfileActivityScreen,
  StudentProfileContactScreen,
  StudentProfileEditScreen,
  StudentProfileGuardianScreen,
  StudentProfilePersonalScreen,
  StudentProfileScreen,
} from "@/features/student/components/screens/profile-screens";
import {
  StudentDocumentsScreen,
  StudentProfileUpdateRequestsScreen,
} from "@/features/student/components/screens/st01-portal-screens";
import { CurriculumScreen } from "@/features/student/components/screens/curriculum-screens";
import { RegistrationScreen } from "@/features/student/components/screens/registration-screens";
import { StudentPortalHomeScreen } from "@/features/student/components/screens/portal-home-screen";
import { TimetableScreen } from "@/features/student/components/screens/timetable-screens";
import { AttendanceScreen } from "@/features/student/components/screens/attendance-screens";
import { CiaScreen } from "@/features/student/components/screens/cia-screens";
import { ContinuousAssessmentScreen } from "@/features/student/components/screens/continuous-assessment-screens";

const ACADEMICS_SLUGS = new Set([
  "academics",
  "enrollment-status",
  "enrollment-history",
  "academic-eligibility",
  "enrollment-requests",
  "new-enrollment-request",
]);

const CURRICULUM_SLUGS = new Set([
  "curriculum",
  "programme-curriculum",
  "enrolled-courses",
  "semester-subjects",
  "course-syllabus",
  "learning-outcomes",
  "course-prerequisites",
  "course-information",
]);

const REGISTRATION_SLUGS = new Set([
  "registration",
  "registration-eligibility",
  "available-courses",
  "elective-groups",
  "my-registrations",
  "submit-registration",
  "registration-history",
]);

const TIMETABLE_SLUGS = new Set([
  "timetable",
  "daily-timetable",
  "weekly-timetable",
  "semester-timetable",
  "academic-calendar",
  "calendar-deadlines",
  "examination-schedule",
  "timetable-changes",
  "timetable-notifications",
  "cancelled-sessions",
]);

const ATTENDANCE_SLUGS = new Set([
  "attendance",
  "attendance-subjects",
  "attendance-daily",
  "attendance-history",
  "attendance-shortages",
  "attendance-eligibility",
  "attendance-export",
  "discrepancy-requests",
  "new-discrepancy-request",
]);

const CIA_SLUGS = new Set([
  "cia",
  "cia-schedules",
  "cia-marks",
  "cia-subject-marks",
  "cia-corrections",
  "cia-history",
  "cia-components",
]);

const CONTINUOUS_ASSESSMENT_SLUGS = new Set([
  "assessments",
  "assignments",
  "assignment-detail",
  "quiz-schedules",
  "quiz-results",
  "assignment-marks",
  "submission-status",
  "assignment-feedback",
  "resubmission-eligibility",
]);

export function StudentScreen({ slug }: { slug: string }) {
  if (slug === "portal-home") return <StudentPortalHomeScreen />;
  if (slug === "dashboard") return <StudentDashboardScreen />;
  if (slug === "profile") return <StudentProfileScreen />;
  if (slug === "profile-personal") return <StudentProfilePersonalScreen />;
  if (slug === "profile-academic") return <StudentProfileAcademicScreen />;
  if (slug === "profile-contact") return <StudentProfileContactScreen />;
  if (slug === "profile-guardian") return <StudentProfileGuardianScreen />;
  if (slug === "profile-edit") return <StudentProfileEditScreen />;
  if (slug === "profile-activity") return <StudentProfileActivityScreen />;
  if (slug === "profile-update-requests") return <StudentProfileUpdateRequestsScreen />;
  if (slug === "documents") return <StudentDocumentsScreen />;
  if (ACADEMICS_SLUGS.has(slug)) {
    return <AcademicsScreen slug={slug as Parameters<typeof AcademicsScreen>[0]["slug"]} />;
  }
  if (CURRICULUM_SLUGS.has(slug)) {
    return <CurriculumScreen slug={slug as Parameters<typeof CurriculumScreen>[0]["slug"]} />;
  }
  if (REGISTRATION_SLUGS.has(slug)) {
    return (
      <RegistrationScreen slug={slug as Parameters<typeof RegistrationScreen>[0]["slug"]} />
    );
  }
  if (TIMETABLE_SLUGS.has(slug)) {
    return <TimetableScreen slug={slug as Parameters<typeof TimetableScreen>[0]["slug"]} />;
  }
  if (ATTENDANCE_SLUGS.has(slug)) {
    return <AttendanceScreen slug={slug as Parameters<typeof AttendanceScreen>[0]["slug"]} />;
  }
  if (CIA_SLUGS.has(slug)) {
    return <CiaScreen slug={slug as Parameters<typeof CiaScreen>[0]["slug"]} />;
  }
  if (CONTINUOUS_ASSESSMENT_SLUGS.has(slug)) {
    return (
      <ContinuousAssessmentScreen
        slug={slug as Parameters<typeof ContinuousAssessmentScreen>[0]["slug"]}
      />
    );
  }
  return null;
}