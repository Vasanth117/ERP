import type { ReactNode } from "react";

import {
  PORTAL_PAGE_DESC,
  STUDENT_TAB_PAGE_TITLE,
} from "@/features/student/components/ui/student-portal-tokens";
import { cn } from "@/lib/utils";

type StudentPageHeadingProps = {
  title: string;
  description?: string;
  figmaFrame?: string;
  actions?: ReactNode;
  className?: string;
};

export function StudentPageHeading({
  title,
  description,
  figmaFrame,
  actions,
  className,
}: StudentPageHeadingProps) {
  return (
    <div
      className={cn(
        "mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between",
        className,
      )}
      data-figma-frame={figmaFrame}
    >
      <div>
        <h2 className={STUDENT_TAB_PAGE_TITLE}>{title}</h2>
        {description ? <p className={PORTAL_PAGE_DESC}>{description}</p> : null}
      </div>
      {actions ? <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div> : null}
    </div>
  );
}