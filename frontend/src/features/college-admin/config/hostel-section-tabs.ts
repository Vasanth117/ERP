/** Figma CA 13 — hostel administration (grouped section nav). */
export const hostelSectionTabs = [
  {
    label: "Overview",
    href: "/college-admin/hostel/hostel-dashboard",
    figmaFrame: "161:2199",
    activePrefixes: ["/college-admin/hostel/hostel-dashboard"],
  },
  {
    label: "Buildings & rooms",
    href: "/college-admin/hostel/hostel-building-management",
    figmaFrame: "161:2589",
    activePrefixes: [
      "/college-admin/hostel/hostel-building-management",
      "/college-admin/hostel/room-management",
    ],
  },
  {
    label: "Admissions & allocation",
    href: "/college-admin/hostel/hostel-admission-applications",
    figmaFrame: "161:3565",
    activePrefixes: [
      "/college-admin/hostel/hostel-admission-applications",
      "/college-admin/hostel/bed-allocation",
    ],
  },
  {
    label: "Residents",
    href: "/college-admin/hostel/resident-management",
    figmaFrame: "161:3875",
    activePrefixes: [
      "/college-admin/hostel/resident-management",
      "/college-admin/hostel/hostel-check-in-checkout",
    ],
  },
  {
    label: "Fees & mess",
    href: "/college-admin/hostel/hostel-fee-management",
    figmaFrame: "161:4530",
    activePrefixes: [
      "/college-admin/hostel/hostel-fee-management",
      "/college-admin/hostel/mess-management",
    ],
  },
  {
    label: "Visitors & outpass",
    href: "/college-admin/hostel/visitor-management",
    figmaFrame: "161:5143",
    activePrefixes: [
      "/college-admin/hostel/visitor-management",
      "/college-admin/hostel/leave-outpass-approval",
    ],
  },
  {
    label: "Maintenance & incidents",
    href: "/college-admin/hostel/maintenance-complaints",
    figmaFrame: "161:5766",
    activePrefixes: [
      "/college-admin/hostel/maintenance-complaints",
      "/college-admin/hostel/hostel-incident-management",
    ],
  },
  {
    label: "Reports & settings",
    href: "/college-admin/hostel/hostel-reports",
    figmaFrame: "161:6367",
    activePrefixes: [
      "/college-admin/hostel/hostel-reports",
      "/college-admin/hostel/hostel-settings",
    ],
  },
] satisfies ReadonlyArray<{
  label: string;
  href: string;
  figmaFrame: string;
  activePrefixes?: string[];
}>;