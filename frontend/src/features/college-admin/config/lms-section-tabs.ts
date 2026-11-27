/** Figma CA 15 — learning management (grouped section nav). */
export const lmsSectionTabs = [
  {
    label: "Overview",
    href: "/college-admin/lms/lms-dashboard",
    figmaFrame: "161:11018",
    activePrefixes: ["/college-admin/lms/lms-dashboard"],
  },
  {
    label: "Courses & mapping",
    href: "/college-admin/lms/course-management",
    figmaFrame: "161:11386",
    activePrefixes: [
      "/college-admin/lms/course-management",
      "/college-admin/lms/subject-course-mapping",
      "/college-admin/lms/course-mappings",
    ],
  },
  {
    label: "Content",
    href: "/college-admin/lms/learning-material-management",
    figmaFrame: "161:12013",
    activePrefixes: [
      "/college-admin/lms/learning-material-management",
      "/college-admin/lms/video-lecture-management",
      "/college-admin/lms/unit-chapter-management",
      "/college-admin/lms/content-categories",
    ],
  },
  {
    label: "Assessments",
    href: "/college-admin/lms/assignment-management",
    figmaFrame: "161:12914",
    activePrefixes: [
      "/college-admin/lms/assignment-management",
      "/college-admin/lms/quiz-management",
      "/college-admin/lms/assessment-management",
    ],
  },
  {
    label: "Progress & faculty content",
    href: "/college-admin/lms/student-learning-progress",
    figmaFrame: "161:13796",
    activePrefixes: [
      "/college-admin/lms/student-learning-progress",
      "/college-admin/lms/faculty-content-management",
    ],
  },
  {
    label: "Reports & settings",
    href: "/college-admin/lms/lms-reports",
    figmaFrame: "161:14368",
    activePrefixes: [
      "/college-admin/lms/lms-reports",
      "/college-admin/lms/lms-settings",
      "/college-admin/lms/lms-configuration-history",
      "/college-admin/lms/lms-monitoring",
    ],
  },
] satisfies ReadonlyArray<{
  label: string;
  href: string;
  figmaFrame: string;
  activePrefixes?: string[];
}>;