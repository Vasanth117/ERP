"use client";

import Link from "next/link";

import type { ErpIconName } from "@/components/icons/erp/names";
import { CollegeAdminSidebarIcon } from "@/features/college-admin/components/layout/college-admin-sidebar-icon";
import {
  CollegeAdminDashboardKpiCard,
  CollegeAdminKpiGrid,
} from "@/features/student/components/ui/student-screen-ui";
import {
  StudentCaPanel,
  StudentPageToolbar,
} from "@/features/student/components/ui/student-ca-panels";
import { studentModuleChrome, type StudentModuleKey } from "@/features/student/config/section-tabs";
import { studentNavGroups, type StudentNavItem } from "@/features/student/config/navigation";
import { studentScreens } from "@/features/student/config/screens";

const MODULE_ORDER: StudentModuleKey[] = [
  "overview",
  "academics",
  "curriculum",
  "registration",
  "timetable",
  "attendance",
  "cia",
  "assessments",
];

const KPI_ICON: Record<StudentModuleKey, ErpIconName> = {
  overview: "layout-dashboard",
  academics: "graduation-cap",
  curriculum: "library-big",
  registration: "clipboard-list",
  timetable: "calendar",
  attendance: "clipboard-check",
  cia: "award",
  assessments: "file-text",
};

function firstLinkForModule(key: StudentModuleKey): string {
  const def = studentModuleChrome[key];
  const group = studentNavGroups.find((g) => g.title === def.navGroupTitle);
  const item = group?.items.find((i) => i.id !== "portal-home") ?? group?.items[0];
  return item?.href ?? "/student/dashboard";
}

function pageCountForModule(figmaPage: string): number {
  return studentScreens.filter((s) => s.figmaPage === figmaPage && s.slug !== "portal-home").length;
}

export function StudentPortalHomeScreen() {
  return (
    <div className="space-y-5" data-figma-page="ST 00">
      <StudentPageToolbar
        title="Workspace map"
        description="Jump into any ST 01–08 area. Use the module tabs above like College Admin, or open a page below."
      />

      <CollegeAdminKpiGrid columns={4}>
        {MODULE_ORDER.map((key, index) => {
          const def = studentModuleChrome[key];
          const count = pageCountForModule(def.figmaPage);
          return (
            <Link key={key} href={firstLinkForModule(key)} className="block">
              <CollegeAdminDashboardKpiCard
                label={def.figmaPage}
                value={count}
                hint={`${count} workspace page${count === 1 ? "" : "s"}`}
                kpiKey={key}
                index={index}
                iconSlug={KPI_ICON[key]}
              />
            </Link>
          );
        })}
      </CollegeAdminKpiGrid>

      <StudentCaPanel title="All pages (ST 01–08)">
        <div className="overflow-x-auto py-2">
          <table className="w-full min-w-[640px] text-left text-[13px]">
            <thead>
              <tr className="border-b border-[#f1f5f9] text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">
                <th className="px-2 py-2.5">Module</th>
                <th className="px-2 py-2.5">Page</th>
                <th className="px-2 py-2.5">Route</th>
                <th className="px-2 py-2.5 text-right">Open</th>
              </tr>
            </thead>
            <tbody>
              {studentScreens
                .filter((s) => s.slug !== "portal-home")
                .map((screen) => (
                  <tr key={screen.slug} className="border-b border-[#f8fafc] hover:bg-[#f8fafc]">
                    <td className="px-2 py-3 font-medium text-[#245dd8]">{screen.figmaPage}</td>
                    <td className="px-2 py-3 text-[#111827]">{screen.title}</td>
                    <td className="px-2 py-3 text-[#9ca3af]">{screen.path}</td>
                    <td className="px-2 py-3 text-right">
                      <Link
                        href={screen.path}
                        className="text-[12px] font-medium text-[#245dd8] hover:underline"
                      >
                        Open →
                      </Link>
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </StudentCaPanel>

      <StudentCaPanel title="Quick navigation by module">
        <div className="grid gap-4 py-3 sm:grid-cols-2">
          {MODULE_ORDER.map((key) => (
            <ModuleQuickList key={key} moduleKey={key} />
          ))}
        </div>
      </StudentCaPanel>
    </div>
  );
}

function ModuleQuickList({ moduleKey }: { moduleKey: StudentModuleKey }) {
  const def = studentModuleChrome[moduleKey];
  const group = studentNavGroups.find((g) => g.title === def.navGroupTitle);
  const items = (group?.items ?? []).filter((i) => i.id !== "portal-home");

  return (
    <div className="rounded-lg border border-[#f1f5f9] bg-[#fafbfc] p-3">
      <p className="text-[11px] font-semibold uppercase tracking-wide text-[#245dd8]">
        {def.figmaPage}
      </p>
      <p className="mt-0.5 text-[13px] font-semibold text-[#111827]">{def.title}</p>
      <ul className="mt-2 space-y-1">
        {items.map((item) => (
          <li key={item.id}>
            <NavRow item={item} />
          </li>
        ))}
      </ul>
    </div>
  );
}

function NavRow({ item }: { item: StudentNavItem }) {
  return (
    <Link
      href={item.href}
      className="flex items-center gap-2 rounded-md px-1 py-1.5 text-[13px] text-[#4b5563] hover:bg-white hover:text-[#245dd8]"
    >
      <CollegeAdminSidebarIcon name={item.icon} size={16} active={false} />
      <span className="truncate">{item.label}</span>
    </Link>
  );
}