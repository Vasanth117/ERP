"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import {
  FormPlaceholder,
  SectionPanel,
} from "@/features/college-admin/components/ui/college-admin-screen-ui";
import { GenericModuleScreen } from "@/features/college-admin/components/modules/generic-module-screen";
import { StatCard } from "@/features/college-admin/components/ui/query-state";
import { resolveModuleEndpoint } from "@/features/college-admin/config/module-endpoint-resolver";

const FORM_SLUGS = new Set([
  "general-ledger",
  "chart-of-accounts",
  "budget-management",
  "department-budget-allocation",
  "income-expense-management",
  "vendor-management",
  "purchase-orders",
  "procurement-management",
  "vendor-payments",
  "expense-reimbursements",
  "bank-reconciliation",
  "financial-period-closing",
]);

export function FinanceExtensionsScreen({ slug, title }: { slug: string; title: string }) {
  const { apiPath, viewType } = resolveModuleEndpoint("finance-extensions", slug);
  if (slug === "institutional-finance-dashboard") {
    return <FinanceExtDashboard />;
  }
  if (slug === "financial-statements" || slug === "tax-compliance-reports") {
    return (
      <GenericModuleScreen
        moduleKey="finance-extensions"
        slug={slug}
        title={title}
        apiPath="/college-admin/finance-extensions/budgets"
        viewType="report"
      />
    );
  }
  if (FORM_SLUGS.has(slug)) {
    return (
      <FormPlaceholder
        title={title}
        description="Institutional finance extensions (Figma CA 22)."
        submitLabel="Submit"
      />
    );
  }
  return (
    <GenericModuleScreen
      moduleKey="finance-extensions"
      slug={slug}
      title={title}
      apiPath={apiPath}
      viewType={viewType}
    />
  );
}

function FinanceExtDashboard() {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Budget modules" value={7} hint="CA 22 extensions" />
        <StatCard label="Procurement" value="Active" hint="Purchase workflow" />
        <Link
          href="/college-admin/finance-extensions/budget-management"
          className="flex items-center text-sm font-medium text-[#245dd8]"
        >
          Budget management →
        </Link>
        <Link
          href="/college-admin/finance-extensions/vendor-management"
          className="flex items-center text-sm font-medium text-[#245dd8]"
        >
          Vendors →
        </Link>
      </div>
      <SectionPanel
        title="Institutional finance"
        description="Configure budgets, vendors, and procurement per Figma CA 22."
      >
        <p className="text-sm text-[#607086]">
          API endpoints under <code>/college-admin/finance-extensions/*</code> back each workflow. Use module tabs to
          open ledger, procurement, and reporting screens.
        </p>
      </SectionPanel>
    </div>
  );
}