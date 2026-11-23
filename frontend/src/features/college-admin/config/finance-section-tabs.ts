/** Figma CA 10 — finance administration (grouped section nav). */
export const financeSectionTabs = [
  {
    label: "Overview",
    href: "/college-admin/finance/finance-dashboard",
    figmaFrame: "160:2199",
    activePrefixes: ["/college-admin/finance/finance-dashboard"],
  },
  {
    label: "Fee structures",
    href: "/college-admin/finance/fee-structure-management",
    figmaFrame: "160:2630",
    activePrefixes: ["/college-admin/finance/fee-structure-management", "/college-admin/finance/fee-structures"],
  },
  {
    label: "Student fees",
    href: "/college-admin/finance/student-fee-management",
    figmaFrame: "160:2938",
    activePrefixes: ["/college-admin/finance/student-fee-management", "/college-admin/finance/fee-assessments"],
  },
  {
    label: "Demands & invoices",
    href: "/college-admin/finance/fee-demand-invoice-management",
    figmaFrame: "160:3264",
  },
  {
    label: "Payments",
    href: "/college-admin/finance/online-payment-monitoring",
    figmaFrame: "160:3595",
    activePrefixes: [
      "/college-admin/finance/online-payment-monitoring",
      "/college-admin/finance/offline-payment-collection",
      "/college-admin/finance/payment-transactions",
      "/college-admin/finance/finance-transactions",
    ],
  },
  {
    label: "Receipts & dues",
    href: "/college-admin/finance/receipt-management",
    figmaFrame: "160:4645",
    activePrefixes: [
      "/college-admin/finance/receipt-management",
      "/college-admin/finance/outstanding-dues-management",
      "/college-admin/finance/student-ledger",
    ],
  },
  {
    label: "Aid & refunds",
    href: "/college-admin/finance/scholarship-management",
    figmaFrame: "160:5293",
    activePrefixes: [
      "/college-admin/finance/scholarship-management",
      "/college-admin/finance/fee-concession-waiver-management",
      "/college-admin/finance/refund-management",
      "/college-admin/finance/refunds",
      "/college-admin/finance/fee-concessions",
    ],
  },
  {
    label: "Reconciliation & reports",
    href: "/college-admin/finance/payment-reconciliation",
    figmaFrame: "160:6226",
    activePrefixes: [
      "/college-admin/finance/payment-reconciliation",
      "/college-admin/finance/financial-reports",
      "/college-admin/finance/finance-summary-report",
    ],
  },
  {
    label: "Settings",
    href: "/college-admin/finance/finance-settings",
    figmaFrame: "160:6843",
  },
] satisfies ReadonlyArray<{
  label: string;
  href: string;
  figmaFrame: string;
  activePrefixes?: string[];
}>;