/** Figma CA 12 — library administration (grouped section nav). */
export const librarySectionTabs = [
  {
    label: "Overview",
    href: "/college-admin/library/library-dashboard",
    figmaFrame: "160:11570",
    activePrefixes: ["/college-admin/library/library-dashboard"],
  },
  {
    label: "Branches & catalogue",
    href: "/college-admin/library/library-branch-management",
    figmaFrame: "160:11930",
    activePrefixes: [
      "/college-admin/library/library-branch-management",
      "/college-admin/library/book-catalogue",
    ],
  },
  {
    label: "Inventory & acquisition",
    href: "/college-admin/library/book-inventory",
    figmaFrame: "160:12552",
    activePrefixes: [
      "/college-admin/library/book-inventory",
      "/college-admin/library/book-acquisition",
    ],
  },
  {
    label: "Circulation",
    href: "/college-admin/library/book-issue-return-management",
    figmaFrame: "160:13164",
    activePrefixes: [
      "/college-admin/library/book-issue-return-management",
      "/college-admin/library/reservation-management",
      "/college-admin/library/library-circulation",
    ],
  },
  {
    label: "Members & fines",
    href: "/college-admin/library/library-member-management",
    figmaFrame: "160:13760",
    activePrefixes: [
      "/college-admin/library/library-member-management",
      "/college-admin/library/fine-management",
      "/college-admin/library/lost-damaged-books",
    ],
  },
  {
    label: "Digital library",
    href: "/college-admin/library/digital-library-management",
    figmaFrame: "160:14657",
    activePrefixes: ["/college-admin/library/digital-library-management"],
  },
  {
    label: "Reports & settings",
    href: "/college-admin/library/library-reports",
    figmaFrame: "160:14947",
    activePrefixes: [
      "/college-admin/library/library-reports",
      "/college-admin/library/library-settings",
      "/college-admin/library/library-summary-report",
    ],
  },
] satisfies ReadonlyArray<{
  label: string;
  href: string;
  figmaFrame: string;
  activePrefixes?: string[];
}>;