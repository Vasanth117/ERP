"use client";

import { ReportsAnalyticsDashboard } from "@/features/college-admin/components/reports/reports-analytics-dashboard";
import { ReportsAcademicModuleDashboard } from "@/features/college-admin/components/reports/reports-academic-module-dashboard";
import { reportsSlugToModule } from "@/features/college-admin/types/reports-academic-module";
import { ReportsCustomBuilderDashboard } from "@/features/college-admin/components/reports/reports-custom-builder-dashboard";
import { ReportsExportHistoryDashboard } from "@/features/college-admin/components/reports/reports-export-history-dashboard";
import { ReportsScheduledDashboard } from "@/features/college-admin/components/reports/reports-scheduled-dashboard";
import { GenericModuleScreen } from "@/features/college-admin/components/modules/generic-module-screen";
import { resolveModuleEndpoint } from "@/features/college-admin/config/module-endpoint-resolver";

const REPORT_SLUGS = new Set<string>();

export function ReportsScreen({ slug, title }: { slug: string; title: string }) {
  const { apiPath, viewType } = resolveModuleEndpoint("reports", slug);
  if (slug === "reports-dashboard" || slug === "analytics-dashboard") {
    return <ReportsAnalyticsDashboard />;
  }
  const modulePage = reportsSlugToModule(slug);
  if (modulePage) {
    return <ReportsAcademicModuleDashboard section={modulePage.section} pageKey={modulePage.pageKey} />;
  }
  if (slug === "custom-report-builder") {
    return <ReportsCustomBuilderDashboard />;
  }
  if (slug === "scheduled-reports") {
    return <ReportsScheduledDashboard />;
  }
  if (slug === "export-download-history") {
    return <ReportsExportHistoryDashboard />;
  }
  if (REPORT_SLUGS.has(slug)) {
    return (
      <GenericModuleScreen
        moduleKey="reports"
        slug={slug}
        title={title}
        apiPath="/college-admin/reports-analytics/definitions"
        viewType="report"
      />
    );
  }
  return (
    <GenericModuleScreen
      moduleKey="reports"
      slug={slug}
      title={title}
      apiPath={apiPath}
      viewType={viewType}
    />
  );
}