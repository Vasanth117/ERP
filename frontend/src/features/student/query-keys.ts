export const studentQueryKeys = {
  all: ["student"] as const,
  dashboard: (range?: string) => [...studentQueryKeys.all, "dashboard", range ?? "week"] as const,
  dashboardStats: () => [...studentQueryKeys.all, "dashboard-stats"] as const,
  dashboardCgpa: () => [...studentQueryKeys.all, "dashboard-cgpa"] as const,
  dashboardBacklog: () => [...studentQueryKeys.all, "dashboard-backlog"] as const,
  dashboardActivities: (limit: number, offset: number) =>
    [...studentQueryKeys.all, "dashboard-activities", limit, offset] as const,
  profile: () => [...studentQueryKeys.all, "profile"] as const,
  profileCorrections: () => [...studentQueryKeys.all, "profile-corrections"] as const,
  recordDocuments: () => [...studentQueryKeys.all, "record-documents"] as const,
  communicationPreferences: () =>
    [...studentQueryKeys.all, "communication-preferences"] as const,
  profileActivities: (limit: number, offset: number) =>
    [...studentQueryKeys.all, "profile-activities", limit, offset] as const,
  academics: () => [...studentQueryKeys.all, "academics"] as const,
  enrollmentStatus: () => [...studentQueryKeys.all, "enrollment-status"] as const,
  enrollmentHistory: (limit: number, offset: number) =>
    [...studentQueryKeys.all, "enrollment-history", limit, offset] as const,
  eligibility: () => [...studentQueryKeys.all, "academic-eligibility"] as const,
  enrollmentRequests: (limit: number, offset: number) =>
    [...studentQueryKeys.all, "enrollment-requests", limit, offset] as const,
  curriculum: () => [...studentQueryKeys.all, "curriculum"] as const,
  curriculumOverview: () => [...studentQueryKeys.all, "curriculum-overview"] as const,
  curriculumSemester: (semester?: number) =>
    [...studentQueryKeys.all, "curriculum-semester", semester ?? "current"] as const,
  curriculumSubjectList: (params?: {
    semester?: number;
    category?: string;
    status?: string;
    q?: string;
  }) => [...studentQueryKeys.all, "curriculum-subject-list", params ?? {}] as const,
  curriculumSubjectDetail: (courseCode: string) =>
    [...studentQueryKeys.all, "curriculum-subject-detail", courseCode] as const,
  curriculumSyllabusPage: (courseCode: string, unitNo?: number) =>
    [...studentQueryKeys.all, "curriculum-syllabus-page", courseCode, unitNo ?? "default"] as const,
  curriculumCategoriesElectives: () =>
    [...studentQueryKeys.all, "curriculum-categories-electives"] as const,
  curriculumHistory: () => [...studentQueryKeys.all, "curriculum-history"] as const,
  enrolledCourses: () => [...studentQueryKeys.all, "enrolled-courses"] as const,
  semesterSubjects: () => [...studentQueryKeys.all, "semester-subjects"] as const,
  syllabus: (courseCode: string, subjectId?: string) =>
    [...studentQueryKeys.all, "syllabus", courseCode, subjectId ?? ""] as const,
  outcomes: (courseCode: string) => [...studentQueryKeys.all, "outcomes", courseCode] as const,
  prerequisites: (courseCode: string) =>
    [...studentQueryKeys.all, "prerequisites", courseCode] as const,
  courseInfo: (courseCode: string) => [...studentQueryKeys.all, "course-info", courseCode] as const,
  subjectsForCourse: (courseCode: string) =>
    [...studentQueryKeys.all, "subjects", courseCode] as const,
  registrationEligibility: () => [...studentQueryKeys.all, "registration-eligibility"] as const,
  registrationOverview: () => [...studentQueryKeys.all, "registration-overview"] as const,
  registrationCoursesPage: (params?: { semester?: string; category?: string; q?: string }) =>
    [...studentQueryKeys.all, "registration-courses-page", params ?? {}] as const,
  registrationCourseDetailPage: (courseCode: string) =>
    [...studentQueryKeys.all, "registration-course-detail", courseCode] as const,
  registrationElectivesPage: () => [...studentQueryKeys.all, "registration-electives-page"] as const,
  registrationReviewPage: () => [...studentQueryKeys.all, "registration-review-page"] as const,
  registrationStatusPage: () => [...studentQueryKeys.all, "registration-status-page"] as const,
  availableCourses: () => [...studentQueryKeys.all, "available-courses"] as const,
  electiveGroups: () => [...studentQueryKeys.all, "elective-groups"] as const,
  electiveOptions: (groupId: string) => [...studentQueryKeys.all, "elective-options", groupId] as const,
  confirmedRegistrations: () => [...studentQueryKeys.all, "confirmed-registrations"] as const,
  registrationHistory: (limit: number, offset: number) =>
    [...studentQueryKeys.all, "registration-history", limit, offset] as const,
  timetableOverview: (date?: string) =>
    [...studentQueryKeys.all, "timetable-overview", date ?? ""] as const,
  timetableDailyPage: (params?: { date?: string; course?: string; slot?: string }) =>
    [...studentQueryKeys.all, "timetable-daily-page", params ?? {}] as const,
  timetableWeeklyPage: (params?: { date?: string; course?: string }) =>
    [...studentQueryKeys.all, "timetable-weekly-page", params ?? {}] as const,
  timetableMonthlyPage: (date?: string) =>
    [...studentQueryKeys.all, "timetable-monthly-page", date ?? ""] as const,
  timetableLaboratoryPage: (params?: { date?: string; course?: string; slot?: string }) =>
    [...studentQueryKeys.all, "timetable-laboratory-page", params ?? {}] as const,
  timetableSessionDetail: (slotId: string, date?: string) =>
    [...studentQueryKeys.all, "timetable-session-detail", slotId, date ?? ""] as const,
  timetableDaily: (date?: string, course?: string) =>
    [...studentQueryKeys.all, "timetable-daily", date ?? "", course ?? ""] as const,
  timetableWeekly: (date?: string, course?: string) =>
    [...studentQueryKeys.all, "timetable-weekly", date ?? "", course ?? ""] as const,
  timetableSemester: (course?: string) =>
    [...studentQueryKeys.all, "timetable-semester", course ?? ""] as const,
  academicCalendar: () => [...studentQueryKeys.all, "academic-calendar"] as const,
  calendarDeadlines: (limit: number, offset: number) =>
    [...studentQueryKeys.all, "calendar-deadlines", limit, offset] as const,
  examinationSchedule: () => [...studentQueryKeys.all, "examination-schedule"] as const,
  timetableChanges: () => [...studentQueryKeys.all, "timetable-changes"] as const,
  timetableNotifications: () => [...studentQueryKeys.all, "timetable-notifications"] as const,
  cancelledSessions: () => [...studentQueryKeys.all, "cancelled-sessions"] as const,
  attendanceSummary: () => [...studentQueryKeys.all, "attendance-summary"] as const,
  attendanceSubjects: () => [...studentQueryKeys.all, "attendance-subjects"] as const,
  attendanceDaily: (date: string) => [...studentQueryKeys.all, "attendance-daily", date] as const,
  attendanceHistory: (limit: number, offset: number) =>
    [...studentQueryKeys.all, "attendance-history", limit, offset] as const,
  attendanceShortages: () => [...studentQueryKeys.all, "attendance-shortages"] as const,
  attendanceEligibility: () => [...studentQueryKeys.all, "attendance-eligibility"] as const,
  attendanceExport: () => [...studentQueryKeys.all, "attendance-export"] as const,
  discrepancyRequests: (limit: number, offset: number) =>
    [...studentQueryKeys.all, "discrepancy-requests", limit, offset] as const,
  ciaSummary: () => [...studentQueryKeys.all, "cia-summary"] as const,
  ciaSchedules: () => [...studentQueryKeys.all, "cia-schedules"] as const,
  ciaMarks: () => [...studentQueryKeys.all, "cia-marks"] as const,
  ciaSubjectMarks: () => [...studentQueryKeys.all, "cia-subject-marks"] as const,
  ciaCorrections: (limit: number, offset: number) =>
    [...studentQueryKeys.all, "cia-corrections", limit, offset] as const,
  ciaHistory: (limit: number, offset: number) =>
    [...studentQueryKeys.all, "cia-history", limit, offset] as const,
  ciaComponents: (assessmentId: string) =>
    [...studentQueryKeys.all, "cia-components", assessmentId] as const,
  assessmentProgress: () => [...studentQueryKeys.all, "assessment-progress"] as const,
  assignments: () => [...studentQueryKeys.all, "assignments"] as const,
  assignmentDetail: (id: string) => [...studentQueryKeys.all, "assignment-detail", id] as const,
  quizSchedules: () => [...studentQueryKeys.all, "quiz-schedules"] as const,
  quizResults: () => [...studentQueryKeys.all, "quiz-results"] as const,
  assignmentMarks: () => [...studentQueryKeys.all, "assignment-marks"] as const,
  submissionStatus: (id: string) => [...studentQueryKeys.all, "submission-status", id] as const,
  assignmentFeedback: (id: string) => [...studentQueryKeys.all, "assignment-feedback", id] as const,
  resubmissionEligibility: (id: string) =>
    [...studentQueryKeys.all, "resubmission-eligibility", id] as const,
};