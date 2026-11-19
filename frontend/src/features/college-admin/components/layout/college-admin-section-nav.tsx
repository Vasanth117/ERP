"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { resolveSectionTabs } from "@/features/college-admin/config/section-tabs";
import { cn } from "@/lib/utils";

export function CollegeAdminSectionNav() {
  const pathname = usePathname();
  const resolved = resolveSectionTabs(pathname);
  if (!resolved) {
    return null;
  }

  const { section, tabs } = resolved;

  return (
    <div className="border-b border-[#dce3ec] bg-white px-8" data-name="Module navigation">
      <div className="flex h-[33px] items-center gap-2 text-[13px] text-[#607086]">
        <span className="font-medium text-[#172b45]">College Admin</span>
        <span aria-hidden className="text-[#8a98aa]">
          /
        </span>
        <span>{section}</span>
      </div>
      <div className="scrollbar-thin flex gap-2 overflow-x-auto pb-1">
        {tabs.map((tab) => {
          const active =
            pathname === tab.href ||
            (tab.href !== "/college-admin/dashboard" &&
              pathname.startsWith(`${tab.href}/`)) ||
            (tab.href === "/college-admin/dashboard" &&
              pathname === "/college-admin/dashboard");

          return (
            <Link
              key={tab.href}
              href={tab.href}
              data-figma-frame={tab.figmaFrame}
              className={cn(
                "shrink-0 border-b-2 px-0 py-3 text-xs font-medium transition-colors",
                active
                  ? "border-[#245dd8] text-[#245dd8]"
                  : "border-transparent text-[#607086] hover:text-[#172b45]",
              )}
            >
              {tab.label}
            </Link>
          );
        })}
      </div>
    </div>
  );
}