"use client";

import { LibraryBookAcquisitionDashboard } from "@/features/college-admin/components/library/library-book-acquisition-dashboard";
import { LibraryDigitalLibraryDashboard } from "@/features/college-admin/components/library/library-digital-library-dashboard";
import { LibraryBookCatalogueDashboard } from "@/features/college-admin/components/library/library-book-catalogue-dashboard";
import { LibraryBookInventoryDashboard } from "@/features/college-admin/components/library/library-book-inventory-dashboard";
import { LibraryBranchManagementDashboard } from "@/features/college-admin/components/library/library-branch-management-dashboard";
import { LibraryCirculationIssueReturnDashboard } from "@/features/college-admin/components/library/library-circulation-issue-return-dashboard";
import { LibraryDashboard } from "@/features/college-admin/components/library/library-dashboard";
import { LibraryFineManagementDashboard } from "@/features/college-admin/components/library/library-fine-management-dashboard";
import { LibraryLostDamagedDashboard } from "@/features/college-admin/components/library/library-lost-damaged-dashboard";
import { LibraryMemberManagementDashboard } from "@/features/college-admin/components/library/library-member-management-dashboard";
import { LibraryReportsDashboard } from "@/features/college-admin/components/library/library-reports-dashboard";
import { LibraryReservationManagementDashboard } from "@/features/college-admin/components/library/library-reservation-management-dashboard";
import { LibrarySettingsDashboard } from "@/features/college-admin/components/library/library-settings-dashboard";
import { GenericModuleScreen } from "@/features/college-admin/components/modules/generic-module-screen";
import { FormPlaceholder } from "@/features/college-admin/components/ui/college-admin-screen-ui";
import { resolveModuleEndpoint } from "@/features/college-admin/config/module-endpoint-resolver";

const FORM_SLUGS = new Set<string>([]);

export function LibraryScreen({ slug, title }: { slug: string; title: string }) {
  const { apiPath, viewType } = resolveModuleEndpoint("library", slug);
  if (slug === "library-dashboard") {
    return <LibraryDashboard />;
  }
  if (slug === "library-branch-management") {
    return <LibraryBranchManagementDashboard />;
  }
  if (slug === "book-catalogue") {
    return <LibraryBookCatalogueDashboard />;
  }
  if (slug === "book-inventory") {
    return <LibraryBookInventoryDashboard />;
  }
  if (slug === "book-acquisition") {
    return <LibraryBookAcquisitionDashboard />;
  }
  if (slug === "library-reports") {
    return <LibraryReportsDashboard />;
  }
  if (slug === "library-summary-report") {
    return (
      <GenericModuleScreen
        moduleKey="library"
        slug={slug}
        title={title}
        apiPath="/college-admin/library-administration/reports/summary"
        viewType="report"
      />
    );
  }
  if (slug === "library-settings") {
    return <LibrarySettingsDashboard />;
  }
  if (slug === "library-circulation" || slug === "book-issue-return-management") {
    return <LibraryCirculationIssueReturnDashboard />;
  }
  if (slug === "reservation-management") {
    return <LibraryReservationManagementDashboard />;
  }
  if (slug === "library-member-management") {
    return <LibraryMemberManagementDashboard />;
  }
  if (slug === "fine-management") {
    return <LibraryFineManagementDashboard />;
  }
  if (slug === "lost-damaged-books") {
    return <LibraryLostDamagedDashboard />;
  }
  if (slug === "digital-library-management") {
    return <LibraryDigitalLibraryDashboard />;
  }
  if (FORM_SLUGS.has(slug)) {
    return (
      <FormPlaceholder title={title} description="Library administration workflow (Figma CA 12)." />
    );
  }
  return (
    <GenericModuleScreen
      moduleKey="library"
      slug={slug}
      title={title}
      apiPath={apiPath}
      viewType={viewType}
    />
  );
}