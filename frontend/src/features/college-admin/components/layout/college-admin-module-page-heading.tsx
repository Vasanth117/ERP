"use client";

import type { ReactNode } from "react";

import { useCollegeAdminSectionLanding } from "@/features/college-admin/hooks/use-college-admin-section-landing";
import { cn } from "@/lib/utils";

type Props = {
  title: ReactNode;
  subtitle?: ReactNode;
  actions?: ReactNode;
  /** When true, always show title even on section Overview landing. */
  forceShowTitle?: boolean;
  className?: string;
};

/**
 * Module page title row. Hides title + subtitle on section Overview landing
 * (module title already shown in section chrome), keeps action buttons.
 */
export function CollegeAdminModulePageHeading({
  title,
  subtitle,
  actions,
  forceShowTitle = false,
  className,
}: Props) {
  const isLanding = useCollegeAdminSectionLanding();
  const showTitle = forceShowTitle || !isLanding;

  if (!showTitle && !actions) return null;

  return (
    <div
      className={cn(
        "flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between",
        !showTitle && actions && "lg:justify-end",
        className,
      )}
    >
      {showTitle ? (
        <div className="min-w-0">
          <h2 className="text-[22px] font-bold tracking-[-0.02em] text-[#111827]">{title}</h2>
          {subtitle ? <p className="mt-1 text-[14px] text-[#6b7280]">{subtitle}</p> : null}
        </div>
      ) : (
        <div className="sr-only">{title}</div>
      )}
      {actions ? <div className="flex shrink-0 flex-wrap gap-2">{actions}</div> : null}
    </div>
  );
}