"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import { usePathname } from "next/navigation";

import type { CollegeAdminTab } from "@/features/college-admin/config/section-tabs";
import { StudentPageTabs } from "@/features/student/components/layout/student-page-tabs";
import { StudentSt01ModuleNav } from "@/features/student/components/layout/student-st01-module-nav";
import { isStudentSt01Path } from "@/features/student/config/st01-tabs";
import {
  resolveStudentModuleKey,
  studentModuleChrome,
  studentPortalModuleTabs,
  studentTabsForModule,
  type StudentModuleKey,
} from "@/features/student/config/section-tabs";
import { PORTAL_MODULE_TITLE } from "@/lib/portal/shell-styles";
import { cn } from "@/lib/utils";

function isPortalModuleTabActive(pathname: string, tab: CollegeAdminTab): boolean {
  const prefixes = tab.activePrefixes?.length ? tab.activePrefixes : [tab.href];
  return prefixes.some(
    (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`),
  );
}

export function StudentPortalChrome({ children }: { children: ReactNode }) {
  const pathname = usePathname() ?? "";
  const moduleKey = resolveStudentModuleKey(pathname);

  if (!moduleKey) {
    return <div className="mx-auto w-full max-w-[1440px]">{children}</div>;
  }

  const def = studentModuleChrome[moduleKey];
  const sectionTabs = studentTabsForModule(moduleKey);

  if (isStudentSt01Path(pathname)) {
    return (
      <div className="mx-auto w-full max-w-[1440px]" data-figma-page="ST 01">
        <StudentSt01ModuleNav />
        {children}
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-[1440px]" data-figma-page={def.figmaPage}>
      <header className="mb-3">
        <h1 className={PORTAL_MODULE_TITLE}>Student Portal</h1>
        <p className="mt-2 max-w-3xl text-[14px] leading-relaxed text-[#6b7280]">
          {moduleSectionSubtitle(moduleKey)}
        </p>
      </header>

      <nav className="mb-4 border-b border-[#e8ecf2]" aria-label="Student modules">
        <div className="scrollbar-thin -mb-px flex flex-nowrap items-end gap-x-5 overflow-x-auto">
          {studentPortalModuleTabs.map((tab) => {
            const active = isPortalModuleTabActive(pathname, tab);
            return (
              <Link
                key={tab.figmaFrame}
                href={tab.href}
                data-figma-frame={tab.figmaFrame}
                className={cn(
                  "relative shrink-0 whitespace-nowrap border-b-2 px-0.5 pb-2.5 pt-0.5 text-[14px] font-medium leading-5 tracking-[-0.01em] transition-colors duration-150",
                  active
                    ? "border-[#245dd8] text-[#245dd8]"
                    : "border-transparent text-[#6b7280] hover:border-[#d1d5db] hover:text-[#111827]",
                )}
              >
                {tab.label}
              </Link>
            );
          })}
        </div>
      </nav>

      <StudentPageTabs tabs={sectionTabs} className="mb-6" />

      <div>{children}</div>
    </div>
  );
}

function moduleSectionSubtitle(key: StudentModuleKey): string {
  return studentModuleChrome[key].description;
}