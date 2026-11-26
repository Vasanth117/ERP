"use client";

import { AcademicsScreen } from "@/features/college-admin/components/modules/academics-screens";
import { AttendanceScreen } from "@/features/college-admin/components/modules/attendance-screens";
import { ExaminationsScreen } from "@/features/college-admin/components/modules/examinations-screens";
import { FacultyScreen } from "@/features/college-admin/components/modules/faculty-screens";
import { CommunicationScreen } from "@/features/college-admin/components/modules/communication-screens";
import { DataImportScreen } from "@/features/college-admin/components/modules/data-import-screens";
import { FinanceExtensionsScreen } from "@/features/college-admin/components/modules/finance-extensions-screens";
import { HelpdeskScreen } from "@/features/college-admin/components/modules/helpdesk-screens";
import { IntegrationsScreen } from "@/features/college-admin/components/modules/integrations-screens";
import { FinanceScreen } from "@/features/college-admin/components/modules/finance-screens";
import { HostelScreen } from "@/features/college-admin/components/modules/hostel-screens";
import { HrScreen } from "@/features/college-admin/components/modules/hr-screens";
import { LibraryScreen } from "@/features/college-admin/components/modules/library-screens";
import { LmsScreen } from "@/features/college-admin/components/modules/lms-screens";
import { ApprovalsScreen } from "@/features/college-admin/components/modules/approvals-screens";
import { OrganizationScreen } from "@/features/college-admin/components/modules/organization-screens";
import { OperationsScreen } from "@/features/college-admin/components/modules/operations-screens";
import { ReportsScreen } from "@/features/college-admin/components/modules/reports-screens";
import { SharedScreen } from "@/features/college-admin/components/modules/shared-screens";
import { SecurityScreen } from "@/features/college-admin/components/modules/security-screens";
import { StudentsScreen } from "@/features/college-admin/components/modules/students-screens";
import { UsersScreen } from "@/features/college-admin/components/modules/users-screens";
import { resolveModuleEndpoint } from "@/features/college-admin/config/module-endpoint-resolver";
import {
  GenericModuleScreen,
  type ModuleViewType,
} from "@/features/college-admin/components/modules/generic-module-screen";
import { ModuleScreenTabs } from "@/features/college-admin/components/modules/module-screen-tabs";
import { PageHeading } from "@/features/college-admin/components/layout/page-heading";
import { frameBySlug } from "@/features/college-admin/config/frame-registry";

type Props = {
  moduleKey: string;
  slug: string;
  figmaNodeId: string;
  title: string;
};

const MODULES_WITH_SECTION_CHROME = new Set([
  "users",
  "organization",
  "academics",
  "students",
  "faculty",
  "attendance",
  "examinations",
  "finance",
  "hr",
  "library",
  "hostel",
]);

export function CollegeAdminFigmaScreen({
  moduleKey,
  slug,
  figmaNodeId,
  title,
}: Props) {
  const usesSectionChrome = MODULES_WITH_SECTION_CHROME.has(moduleKey);
  const financeOwnHeader = new Set([
    "finance-dashboard",
    "fee-structure-management",
    "student-fee-management",
    "fee-demand-invoice-management",
    "online-payment-monitoring",
    "offline-payment-collection",
    "payment-transactions",
    "receipt-management",
    "outstanding-dues-management",
    "scholarship-management",
    "fee-concession-waiver-management",
    "refund-management",
    "payment-reconciliation",
    "financial-reports",
    "finance-settings",
  ]);
  const showPageHeading =
    !usesSectionChrome || (moduleKey === "finance" && !financeOwnHeader.has(slug));

  return (
    <div data-figma-frame={figmaNodeId}>
      {showPageHeading ? (
        <PageHeading title={title} figmaFrame={figmaNodeId} />
      ) : null}
      {!usesSectionChrome ? (
        <ModuleScreenTabs moduleKey={moduleKey} />
      ) : null}
      <ScreenBody
        moduleKey={moduleKey}
        slug={slug}
        title={title}
      />
    </div>
  );
}

function ScreenBody({
  moduleKey,
  slug,
  title,
}: {
  moduleKey: string;
  slug: string;
  title: string;
}) {
  if (moduleKey === "users") {
    return <UsersScreen slug={slug} />;
  }
  if (moduleKey === "organization") {
    return <OrganizationScreen slug={slug} />;
  }
  if (moduleKey === "academics") {
    return <AcademicsScreen slug={slug} />;
  }
  if (moduleKey === "students") {
    return <StudentsScreen slug={slug} />;
  }
  if (moduleKey === "faculty") {
    return <FacultyScreen slug={slug} title={title} />;
  }
  if (moduleKey === "attendance") {
    return <AttendanceScreen slug={slug} title={title} />;
  }
  if (moduleKey === "examinations") {
    return <ExaminationsScreen slug={slug} title={title} />;
  }
  if (moduleKey === "finance") {
    return <FinanceScreen slug={slug} title={title} />;
  }
  if (moduleKey === "hr") {
    return <HrScreen slug={slug} title={title} />;
  }
  if (moduleKey === "library") {
    return <LibraryScreen slug={slug} title={title} />;
  }
  if (moduleKey === "hostel") {
    return <HostelScreen slug={slug} title={title} />;
  }
  if (moduleKey === "communication") {
    return <CommunicationScreen slug={slug} title={title} />;
  }
  if (moduleKey === "lms") {
    return <LmsScreen slug={slug} title={title} />;
  }
  if (moduleKey === "reports") {
    return <ReportsScreen slug={slug} title={title} />;
  }
  if (moduleKey === "approvals") {
    return <ApprovalsScreen slug={slug} title={title} />;
  }
  if (moduleKey === "security") {
    return <SecurityScreen slug={slug} title={title} />;
  }
  if (moduleKey === "data-import") {
    return <DataImportScreen slug={slug} title={title} />;
  }
  if (moduleKey === "integrations") {
    return <IntegrationsScreen slug={slug} title={title} />;
  }
  if (moduleKey === "helpdesk") {
    return <HelpdeskScreen slug={slug} title={title} />;
  }
  if (moduleKey === "finance-extensions") {
    return <FinanceExtensionsScreen slug={slug} title={title} />;
  }
  if (moduleKey === "operations") {
    return <OperationsScreen slug={slug} title={title} />;
  }
  if (moduleKey === "shared") {
    return <SharedScreen slug={slug} title={title} />;
  }
  const frame = frameBySlug(moduleKey, slug);
  const resolved = resolveModuleEndpoint(moduleKey, slug);
  const apiPath =
    frame && "apiPath" in frame && frame.apiPath
      ? (frame.apiPath as string)
      : resolved.apiPath;
  const viewType =
    frame && "viewType" in frame && frame.viewType
      ? (frame.viewType as ModuleViewType)
      : resolved.viewType;

  return (
    <GenericModuleScreen
      moduleKey={moduleKey}
      slug={slug}
      title={title}
      apiPath={apiPath}
      viewType={viewType}
    />
  );
}