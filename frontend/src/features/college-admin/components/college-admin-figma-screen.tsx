"use client";

import { AcademicsScreen } from "@/features/college-admin/components/modules/academics-screens";
import { OrganizationScreen } from "@/features/college-admin/components/modules/organization-screens";
import { StudentsScreen } from "@/features/college-admin/components/modules/students-screens";
import { UsersScreen } from "@/features/college-admin/components/modules/users-screens";
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

export function CollegeAdminFigmaScreen({
  moduleKey,
  slug,
  figmaNodeId,
  title,
}: Props) {
  return (
    <div data-figma-frame={figmaNodeId}>
      <PageHeading title={title} figmaFrame={figmaNodeId} />
      <ModuleScreenTabs moduleKey={moduleKey} />
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
  const frame = frameBySlug(moduleKey, slug);
  const apiPath =
    frame && "apiPath" in frame ? (frame.apiPath as string | undefined) : undefined;
  const viewType =
    frame && "viewType" in frame
      ? (frame.viewType as ModuleViewType | undefined)
      : undefined;

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