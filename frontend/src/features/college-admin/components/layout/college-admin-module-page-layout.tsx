"use client";

import { Children, type ReactNode } from "react";

import { CollegeAdminModuleInnerSubNav } from "@/features/college-admin/components/layout/college-admin-module-inner-sub-nav";
import { cn } from "@/lib/utils";

type Props = {
  figmaFrame?: string;
  className?: string;
  children: ReactNode;
  /** When false, skips inner pill row (e.g. generic list screens). Default true. */
  showInnerSubNav?: boolean;
};

/**
 * Standard college-admin module page shell: first child is the title row;
 * grouped section pills render under it, then the rest of the page.
 */
export function CollegeAdminModulePageLayout({
  figmaFrame,
  className,
  children,
  showInnerSubNav = true,
}: Props) {
  const items = Children.toArray(children);
  const [first, ...rest] = items;

  return (
    <div className={cn("space-y-5", className)} data-figma-frame={figmaFrame}>
      {first}
      {showInnerSubNav ? (
        <div className="mb-1 pb-4">
          <CollegeAdminModuleInnerSubNav />
        </div>
      ) : null}
      {rest}
    </div>
  );
}