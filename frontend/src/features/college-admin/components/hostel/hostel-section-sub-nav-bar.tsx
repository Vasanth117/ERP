"use client";

import { usePathname } from "next/navigation";

import { CollegeAdminSectionNav } from "@/features/college-admin/components/ui/college-admin-section-nav";
import { useHostelSectionSubNav } from "@/features/college-admin/hooks/use-hostel-section-sub-nav";

export function HostelSectionSubNavBar() {
  const pathname = usePathname() ?? "";
  const { data } = useHostelSectionSubNav(pathname);

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