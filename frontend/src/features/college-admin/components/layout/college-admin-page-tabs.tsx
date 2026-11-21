"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import type { CollegeAdminTab } from "@/features/college-admin/config/section-tabs";
import { cn } from "@/lib/utils";

function isTabActive(pathname: string, tab: CollegeAdminTab): boolean {
  const { href, activePrefixes } = tab;
  if (activePrefixes?.length) {
    return activePrefixes.some(
      (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`),
    );
  }
  if (href === "/college-admin/dashboard") {
    return pathname === href;
  }
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function CollegeAdminPageTabs({
  tabs,
  className,
}: {
  tabs: CollegeAdminTab[];
  className?: string;
}) {
  const pathname = usePathname();
  const items = tabs ?? [];

  if (items.length === 0) {
    return null;
  }

  return (
    <nav
      className={cn("border-b border-[#e8ecf2]", className)}
      aria-label="Section navigation"
    >
      <div className="scrollbar-thin -mb-px flex flex-nowrap items-end gap-x-5 overflow-x-auto">
        {items.map((tab) => {
          const active = isTabActive(pathname, tab);
          return (
            <Link
              key={tab.href}
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
  );
}