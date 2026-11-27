"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import type { CollegeAdminTab } from "@/features/college-admin/config/section-tabs";
import { isStudentSt04Path, isStudentSt04TabActive } from "@/features/student/config/st04-tabs";
import { isStudentSt05Path, isStudentSt05TabActive } from "@/features/student/config/st05-tabs";
import { isStudentTabActive } from "@/features/student/config/section-tabs";
import { cn } from "@/lib/utils";

export function StudentPageTabs({
  tabs,
  className,
}: {
  tabs: CollegeAdminTab[];
  className?: string;
}) {
  const pathname = usePathname() ?? "";
  if (!tabs.length) return null;

  return (
    <nav className={cn("border-b border-[#e8ecf2]", className)} aria-label="Section navigation">
      <div className="scrollbar-thin -mb-px flex flex-nowrap items-end gap-x-5 overflow-x-auto">
        {tabs.map((tab) => {
          const active = isStudentSt05Path(pathname)
            ? isStudentSt05TabActive(pathname, tab)
            : isStudentSt04Path(pathname)
              ? isStudentSt04TabActive(pathname, tab)
              : isStudentTabActive(pathname, tab);
          return (
            <Link
              key={`${tab.href}-${tab.figmaFrame ?? ""}`}
              href={tab.href}
              {...(tab.figmaFrame ? { "data-figma-frame": tab.figmaFrame } : {})}
              suppressHydrationWarning
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