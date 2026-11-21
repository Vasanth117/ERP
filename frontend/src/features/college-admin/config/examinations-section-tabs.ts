/** Figma CA 09 — examination administration (section nav). */
export const examinationsSectionTabs = [
  {
    label: "Overview",
    href: "/college-admin/examinations/examination-dashboard",
    figmaFrame: "159:10708",
    activePrefixes: ["/college-admin/examinations/examination-dashboard"],
  },
  {
    label: "Sessions & setup",
    href: "/college-admin/examinations/examination-session-management",
    figmaFrame: "159:11129",
    activePrefixes: [
      "/college-admin/examinations/examination-session-management",
      "/college-admin/examinations/examination-configuration",
      "/college-admin/examinations/exam-configuration",
      "/college-admin/examinations/exam-seasons",
    ],
  },
  {
    label: "Timetable",
    href: "/college-admin/examinations/exam-timetable-management",
    figmaFrame: "159:11789",
  },
  {
    label: "Registration & eligibility",
    href: "/college-admin/examinations/exam-registration-management",
    figmaFrame: "159:12120",
    activePrefixes: [
      "/college-admin/examinations/exam-registration-management",
      "/college-admin/examinations/student-exam-eligibility",
      "/college-admin/examinations/eligibility-registry",
      "/college-admin/examinations/hall-ticket-administration",
      "/college-admin/examinations/hall-tickets",
    ],
  },
  {
    label: "Halls & invigilation",
    href: "/college-admin/examinations/examination-hall-seating-management",
    figmaFrame: "159:13128",
    activePrefixes: [
      "/college-admin/examinations/examination-hall-seating-management",
      "/college-admin/examinations/invigilator-allocation",
    ],
  },
  {
    label: "Marks & assessment",
    href: "/college-admin/examinations/marks-entry-management",
    figmaFrame: "159:13777",
    activePrefixes: [
      "/college-admin/examinations/marks-entry-management",
      "/college-admin/examinations/internal-external-assessment",
      "/college-admin/examinations/pending-marks-review",
    ],
  },
  {
    label: "Results",
    href: "/college-admin/examinations/result-processing",
    figmaFrame: "159:14699",
    activePrefixes: [
      "/college-admin/examinations/result-processing",
      "/college-admin/examinations/result-approval",
      "/college-admin/examinations/result-publication",
      "/college-admin/examinations/results-publication",
    ],
  },
  {
    label: "Revaluation & supplementary",
    href: "/college-admin/examinations/revaluation-management",
    figmaFrame: "159:15302",
    activePrefixes: [
      "/college-admin/examinations/revaluation-management",
      "/college-admin/examinations/supplementary-examination-management",
    ],
  },
  {
    label: "Reports",
    href: "/college-admin/examinations/examination-reports",
    figmaFrame: "159:15909",
  },
] satisfies ReadonlyArray<{
  label: string;
  href: string;
  figmaFrame: string;
  activePrefixes?: string[];
}>;