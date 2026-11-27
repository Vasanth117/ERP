/** Figma CA 14 — communication administration (grouped section nav). */
export const communicationSectionTabs = [
  {
    label: "Overview",
    href: "/college-admin/communication/communication-dashboard",
    figmaFrame: "161:6942",
    activePrefixes: ["/college-admin/communication/communication-dashboard"],
  },
  {
    label: "Announcements",
    href: "/college-admin/communication/announcements-management",
    figmaFrame: "161:7309",
    activePrefixes: [
      "/college-admin/communication/announcements-management",
      "/college-admin/communication/create-announcement",
    ],
  },
  {
    label: "Audience notifications",
    href: "/college-admin/communication/student-notifications",
    figmaFrame: "161:7956",
    activePrefixes: [
      "/college-admin/communication/student-notifications",
      "/college-admin/communication/faculty-notifications",
      "/college-admin/communication/parent-communication",
    ],
  },
  {
    label: "Channels",
    href: "/college-admin/communication/email-communication",
    figmaFrame: "161:8858",
    activePrefixes: [
      "/college-admin/communication/email-communication",
      "/college-admin/communication/sms-communication",
      "/college-admin/communication/whatsapp-communication",
    ],
  },
  {
    label: "Templates & scheduling",
    href: "/college-admin/communication/communication-templates",
    figmaFrame: "161:9765",
    activePrefixes: [
      "/college-admin/communication/communication-templates",
      "/college-admin/communication/scheduled-messages",
    ],
  },
  {
    label: "Delivery & history",
    href: "/college-admin/communication/delivery-status-monitoring",
    figmaFrame: "161:10356",
    activePrefixes: [
      "/college-admin/communication/delivery-status-monitoring",
      "/college-admin/communication/communication-history",
    ],
  },
] satisfies ReadonlyArray<{
  label: string;
  href: string;
  figmaFrame: string;
  activePrefixes?: string[];
}>;