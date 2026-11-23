"use client";

import { FeeDemandInvoiceManagementDashboard } from "@/features/college-admin/components/finance/fee-demand-invoice-management-dashboard";
import { FeeStructureManagementDashboard } from "@/features/college-admin/components/finance/fee-structure-management-dashboard";
import { OfflinePaymentCollectionDashboard } from "@/features/college-admin/components/finance/offline-payment-collection-dashboard";
import { OnlinePaymentMonitoringDashboard } from "@/features/college-admin/components/finance/online-payment-monitoring-dashboard";
import { OutstandingDuesManagementDashboard } from "@/features/college-admin/components/finance/outstanding-dues-management-dashboard";
import { PaymentTransactionsDashboard } from "@/features/college-admin/components/finance/payment-transactions-dashboard";
import { ReceiptManagementDashboard } from "@/features/college-admin/components/finance/receipt-management-dashboard";
import { StudentFeeManagementDashboard } from "@/features/college-admin/components/finance/student-fee-management-dashboard";
import { FeeConcessionWaiverManagementDashboard } from "@/features/college-admin/components/finance/fee-concession-waiver-management-dashboard";
import { RefundManagementDashboard } from "@/features/college-admin/components/finance/refund-management-dashboard";
import { ScholarshipManagementDashboard } from "@/features/college-admin/components/finance/scholarship-management-dashboard";
import { FinancialReportsDashboard } from "@/features/college-admin/components/finance/financial-reports-dashboard";
import { PaymentReconciliationDashboard } from "@/features/college-admin/components/finance/payment-reconciliation-dashboard";
import { FinanceSettingsDashboard } from "@/features/college-admin/components/finance/finance-settings-dashboard";
import { FinanceDashboard } from "@/features/college-admin/components/finance/finance-dashboard";
import { FormPlaceholder } from "@/features/college-admin/components/ui/college-admin-screen-ui";
import { GenericModuleScreen } from "@/features/college-admin/components/modules/generic-module-screen";
import { resolveModuleEndpoint } from "@/features/college-admin/config/module-endpoint-resolver";

const FORM_SLUGS = new Set<string>();

export function FinanceScreen({ slug, title }: { slug: string; title: string }) {
  const { apiPath, viewType } = resolveModuleEndpoint("finance", slug);
  if (slug === "finance-dashboard") {
    return <FinanceDashboard />;
  }
  if (slug === "fee-structure-management") {
    return <FeeStructureManagementDashboard />;
  }
  if (slug === "student-fee-management") {
    return <StudentFeeManagementDashboard />;
  }
  if (slug === "fee-demand-invoice-management") {
    return <FeeDemandInvoiceManagementDashboard />;
  }
  if (slug === "online-payment-monitoring") {
    return <OnlinePaymentMonitoringDashboard />;
  }
  if (slug === "offline-payment-collection") {
    return <OfflinePaymentCollectionDashboard />;
  }
  if (slug === "payment-transactions") {
    return <PaymentTransactionsDashboard />;
  }
  if (slug === "receipt-management") {
    return <ReceiptManagementDashboard />;
  }
  if (slug === "outstanding-dues-management") {
    return <OutstandingDuesManagementDashboard />;
  }
  if (slug === "scholarship-management") {
    return <ScholarshipManagementDashboard />;
  }
  if (slug === "fee-concession-waiver-management") {
    return <FeeConcessionWaiverManagementDashboard />;
  }
  if (slug === "refund-management") {
    return <RefundManagementDashboard />;
  }
  if (slug === "payment-reconciliation") {
    return <PaymentReconciliationDashboard />;
  }
  if (slug === "financial-reports") {
    return <FinancialReportsDashboard />;
  }
  if (slug === "finance-settings") {
    return <FinanceSettingsDashboard />;
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