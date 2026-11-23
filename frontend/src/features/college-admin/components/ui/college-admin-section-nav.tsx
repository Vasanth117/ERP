"use client";

import Link from "next/link";

import { CollegeAdminSectionNavIcon } from "@/features/college-admin/components/ui/college-admin-section-nav-icons";
import { cn } from "@/lib/utils";

export type CollegeAdminSectionNavItem = {
  key: string;
  label: string;
  active: boolean;
  href?: string;
};

function itemClassName(active: boolean) {
  return cn(
    "inline-flex items-center gap-2 rounded-lg px-3.5 py-2 text-[13px] font-medium transition-colors",
    active
      ? "border border-[#c9d9f7] bg-[#eff6ff] text-[#245dd8] shadow-[0_1px_2px_rgba(36,93,216,0.08)]"
      : "border border-transparent text-[#6b7280] hover:bg-[#f9fafb] hover:text-[#374151]",
  );
}

function NavItemContent({ item }: { item: CollegeAdminSectionNavItem }) {
  return (
    <>
      <CollegeAdminSectionNavIcon
        navKey={item.key}
        className={cn("size-4", item.active ? "text-[#245dd8]" : "text-[#9ca3af]")}
      />
      <span>{item.label}</span>
    </>
  );
}

export function CollegeAdminSectionNav({
  items,
  className,
  onSelect,
  showIcons = true,
}: {
  items: CollegeAdminSectionNavItem[];
  className?: string;
  onSelect?: (key: string) => void;
  showIcons?: boolean;
}) {
  if (!items.length) return null;

  return (
    <nav className={cn("flex flex-wrap items-center gap-1", className)} aria-label="Section navigation">
      {items.map((item) => {
        const classes = itemClassName(item.active);
        const content = showIcons ? (
          <NavItemContent item={item} />
        ) : (
          <span>{item.label}</span>
        );

        if (onSelect || !item.href) {
          return (
            <button
              key={item.key}
              type="button"
              onClick={() => onSelect?.(item.key)}
              className={classes}
              aria-current={item.active ? "page" : undefined}
            >
              {content}
            </button>
          );
        }

        return (
          <Link
            key={item.key}
            href={item.href}
            className={classes}
            aria-current={item.active ? "page" : undefined}
          >
            {content}
          </Link>
        );
      })}
    </nav>
  );
}