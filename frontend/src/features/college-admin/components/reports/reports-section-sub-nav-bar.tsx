"use client";

import { usePathname } from "next/navigation";

import { CollegeAdminSectionNav } from "@/features/college-admin/components/ui/college-admin-section-nav";
import { useReportsSectionSubNav } from "@/features/college-admin/hooks/use-reports-dashboard";

export function ReportsSectionSubNavBar() {
  const pathname = usePathname() ?? "";
  const { data } = useReportsSectionSubNav(pathname);

  if (!data?.items?.length || data.items.length < 2) {
    return null;
  }

  return (
    <CollegeAdminSectionNav
      className="mb-0"
      items={data.items.map((item) => ({
        key: item.icon_key || item.key,
        label: item.label,
        href: item.href,
        active: item.active,
      }))}
    />
  );
}