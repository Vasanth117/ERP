"use client";

import Link from "next/link";

import type { YearsSemestersSubNavItem } from "@/features/college-admin/types/academic-year-management";
import { cn } from "@/lib/utils";

export function CourseCurriculumSubNav({ items }: { items: YearsSemestersSubNavItem[] }) {
  if (!items.length) return null;
  return (
    <div className="inline-flex flex-wrap rounded-lg border border-[#e8ecf2] bg-[#f9fafb] p-1">
      {items.map((item) => (
        <Link
          key={item.key}
          href={item.href}
          className={cn(
            "rounded-md px-3.5 py-1.5 text-[13px] font-medium transition-colors",
            item.active
              ? "bg-white text-[#245dd8] shadow-[0_1px_2px_rgba(15,23,42,0.06)]"
              : "text-[#6b7280] hover:text-[#111827]",
          )}
        >
          {item.label}
        </Link>
      ))}
    </div>
  );
}