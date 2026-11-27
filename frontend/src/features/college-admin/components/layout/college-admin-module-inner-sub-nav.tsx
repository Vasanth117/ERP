"use client";

import type { ComponentType } from "react";
import { usePathname } from "next/navigation";

import { AttendanceSectionSubNavBar } from "@/features/college-admin/components/attendance/attendance-section-sub-nav-bar";
import { CommunicationSectionSubNavBar } from "@/features/college-admin/components/communication/communication-section-sub-nav-bar";
import { HostelSectionSubNavBar } from "@/features/college-admin/components/hostel/hostel-section-sub-nav-bar";
import { LibrarySectionSubNavBar } from "@/features/college-admin/components/library/library-section-sub-nav-bar";
import { LmsSectionSubNavBar } from "@/features/college-admin/components/lms/lms-section-sub-nav-bar";
import { ReportsSectionSubNavBar } from "@/features/college-admin/components/reports/reports-section-sub-nav-bar";

const MODULE_SUB_NAV: ReadonlyArray<{ prefix: string; SubNav: ComponentType }> = [
  { prefix: "/college-admin/attendance/", SubNav: AttendanceSectionSubNavBar },
  { prefix: "/college-admin/reports/", SubNav: ReportsSectionSubNavBar },
  { prefix: "/college-admin/lms/", SubNav: LmsSectionSubNavBar },
  { prefix: "/college-admin/library/", SubNav: LibrarySectionSubNavBar },
  { prefix: "/college-admin/hostel/", SubNav: HostelSectionSubNavBar },
  { prefix: "/college-admin/communication/", SubNav: CommunicationSectionSubNavBar },
];

export function CollegeAdminModuleInnerSubNav() {
  const pathname = usePathname() ?? "";
  const match = MODULE_SUB_NAV.find((entry) => pathname.startsWith(entry.prefix));
  if (!match) return null;
  const SubNav = match.SubNav;
  return <SubNav />;
}