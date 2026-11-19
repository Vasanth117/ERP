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
        <h1 className="text-2xl font-semibold text-[#172b45]">{title}</h1>
        {description ? (
          <p className="mt-1 max-w-2xl text-sm text-[#607086]">{description}</p>
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