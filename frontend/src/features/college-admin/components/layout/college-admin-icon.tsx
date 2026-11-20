"use client";

import { ErpIcon } from "@/components/icons/erp/erp-icon";
import type { ErpIconName } from "@/components/icons/erp/names";
import {
  getCollegeAdminErpIcon,
  resolveCollegeAdminIconSlug,
} from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { cn } from "@/lib/utils";

export function CollegeAdminIcon({
  name,
  size = 16,
  className,
}: {
  name: string;
  size?: number;
  className?: string;
}) {
  const slug = resolveCollegeAdminIconSlug(name);
  const Icon = getCollegeAdminErpIcon(slug);

  const dim = { width: size, height: size, style: { width: size, height: size } };

  if (Icon) {
    return (
      <Icon
        {...dim}
        className={cn("!size-auto shrink-0", className)}
        aria-hidden
      />
    );
  }

  return (
    <ErpIcon
      name={slug as ErpIconName}
      {...dim}
      className={cn("!size-auto shrink-0", className)}
      aria-hidden
    />
  );
}