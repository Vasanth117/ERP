"use client";

import Link from "next/link";
import { useCollegeAdminQuery as useQuery } from "@/features/college-admin/hooks/use-college-admin-query";

import { apiRequest } from "@/lib/api/client";
import {
  DataTable,
  FormPlaceholder,
  SectionPanel,
  ToolbarRow,
  columnsFromRows,
  rowsFromApi,
} from "@/features/college-admin/components/ui/college-admin-screen-ui";
import { GenericModuleScreen } from "@/features/college-admin/components/modules/generic-module-screen";
import {
  QueryState,
  StatCard,
} from "@/features/college-admin/components/ui/query-state";
import { resolveModuleEndpoint } from "@/features/college-admin/config/module-endpoint-resolver";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

function formatMoney(value: number) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value);
}

const FORM_SLUGS = new Set([
  "fee-structure-management",
  "student-fee-management",
  "fee-demand-invoice-management",
  "offline-payment-collection",
  "receipt-management",
  "scholarship-management",
  "fee-concession-waiver-management",
  "refund-management",
  "payment-reconciliation",
  "finance-settings",
]);

export function FinanceScreen({ slug, title }: { slug: string; title: string }) {
  const { apiPath, viewType } = resolveModuleEndpoint("finance", slug);
  if (slug === "finance-dashboard") {
    return <FinanceDashboard />;
  }
  if (slug === "online-payment-monitoring" || slug === "outstanding-dues-management") {
    return (
      <GenericModuleScreen
        moduleKey="finance"
        slug={slug}
        title={title}
        apiPath="/college-admin/finance-administration/transactions"
        viewType="report"
      />
    );
  }
  if (FORM_SLUGS.has(slug)) {
    return (
      <FormPlaceholder title={title} description="Finance administration form (Figma CA 10)." />
    );
  }
  return (
    <GenericModuleScreen
      moduleKey="finance"
      slug={slug}
      title={title}
      apiPath={apiPath}
      viewType={viewType}
    />
  );
}

function FinanceDashboard() {
  const summary = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "finance-summary"],
    queryFn: () =>
      apiRequest<{
        collected_amount?: number;
        outstanding_amount?: number;
        open_demands?: number;
      }>("/college-admin/finance-administration/reports/summary"),
  });
  const tx = useQuery({
    queryKey: [...collegeAdminQueryKeys.all, "finance-tx"],
    queryFn: () =>
      apiRequest<{ items?: unknown[] }>(
        "/college-admin/finance-administration/transactions?limit=20&offset=0",
      ),
  });
  const rows = rowsFromApi(tx.data?.items);
  return (
    <QueryState
      isLoading={summary.isLoading}
      isError={summary.isError}
      error={summary.error}
      onRetry={() => void summary.refetch()}
    >
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Collected"
          value={formatMoney(summary.data?.collected_amount ?? 0)}
        />
        <StatCard
          label="Outstanding"
          value={formatMoney(summary.data?.outstanding_amount ?? 0)}
        />
        <StatCard label="Open demands" value={summary.data?.open_demands ?? 0} />
        <Link
          href="/college-admin/finance/payment-transactions"
          className="flex items-center text-sm font-medium text-[#245dd8]"
        >
          All transactions →
        </Link>
      </div>
      <SectionPanel title="Recent transactions" className="mt-6">
        <ToolbarRow
          onRefresh={() => {
            void summary.refetch();
            void tx.refetch();
          }}
        />
        <DataTable columns={columnsFromRows(rows)} rows={rows} />
      </SectionPanel>
    </QueryState>
  );
}