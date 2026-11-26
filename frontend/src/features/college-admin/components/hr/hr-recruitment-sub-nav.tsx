"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import type { HrRecruitmentSubNavItem } from "@/features/college-admin/types/hr-recruitment";
import { cn } from "@/lib/utils";

export function HrRecruitmentSubNav({ items }: { items: HrRecruitmentSubNavItem[] }) {
  const pathname = usePathname() ?? "";
  if (!items.length) return null;

  return (
    <nav
      className="border-b border-[#e8ecf2]"
      aria-label="Recruitment and onboarding sections"
    >
      <div className="scrollbar-thin -mb-px flex flex-nowrap items-end gap-x-5 overflow-x-auto">
        {items.map((item) => {
          const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.key}
              href={item.href}
              className={cn(
                "relative shrink-0 whitespace-nowrap border-b-2 px-0.5 pb-2.5 pt-0.5 text-[14px] font-medium leading-5 tracking-[-0.01em] transition-colors duration-150",
                active
                  ? "border-[#245dd8] text-[#245dd8]"
                  : "border-transparent text-[#6b7280] hover:border-[#d1d5db] hover:text-[#111827]",
              )}
            >
              {item.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}