import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";

type PageHeadingProps = {
  title: string;
  description?: string;
  figmaFrame?: string;
  actions?: ReactNode;
  onRefresh?: () => void;
};

export function PageHeading({
  title,
  description,
  figmaFrame,
  actions,
  onRefresh,
}: PageHeadingProps) {
  return (
    <div
      className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between"
      data-figma-frame={figmaFrame}
    >
      <div>
        <h2 className="text-[18px] font-semibold tracking-[-0.01em] text-[#111827]">
          {title}
        </h2>
        {description ? (
          <p className="mt-1.5 max-w-2xl text-[14px] leading-relaxed text-[#6b7280]">
            {description}
          </p>
        ) : null}
      </div>
      <div className="flex shrink-0 items-center gap-2">
        {onRefresh ? (
          <Button
            type="button"
            variant="outline"
            className="h-9 border-[#dce3ec] text-xs"
            onClick={onRefresh}
          >
            Refresh
          </Button>
        ) : null}
        {actions}
      </div>
    </div>
  );
}