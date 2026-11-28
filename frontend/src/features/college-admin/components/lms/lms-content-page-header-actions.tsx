"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import { UploadIcon } from "@/components/icons/erp/generated/upload";
import { Button } from "@/components/ui/button";
import { CollegeAdminDownload } from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { CollegeAdminPlusActionLabel } from "@/features/college-admin/components/ui/college-admin-plus-action";

type Props = {
  exportLabel?: string;
  exportDisabled?: boolean;
  onExport?: () => void;
  primaryHref?: string;
  primaryLabel?: string;
  primaryMode?: "upload" | "plus";
  onPrimaryClick?: () => void;
  primaryNode?: ReactNode;
};

export function LmsContentPageHeaderActions({
  exportLabel = "Export",
  exportDisabled,
  onExport,
  primaryHref,
  primaryLabel,
  primaryMode = "upload",
  onPrimaryClick,
  primaryNode,
}: Props) {
  return (
    <div className="flex flex-wrap items-center justify-end gap-2">
      {onExport ? (
        <Button
          type="button"
          variant="outline"
          className="h-9 gap-1.5 border-[#dce3ec] text-xs font-medium text-[#374151]"
          disabled={exportDisabled}
          onClick={onExport}
        >
          <CollegeAdminDownload className="size-3.5" aria-hidden />
          {exportLabel}
        </Button>
      ) : null}
      {primaryNode}
      {primaryHref && primaryLabel ? (
        <Link
          href={primaryHref}
          className="inline-flex h-9 shrink-0 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
        >
          {primaryMode === "upload" ? <UploadIcon className="size-3.5" aria-hidden /> : null}
          {primaryMode === "plus" ? (
            <CollegeAdminPlusActionLabel iconClassName="size-3.5" label={primaryLabel} />
          ) : (
            primaryLabel
          )}
        </Link>
      ) : null}
      {onPrimaryClick && primaryLabel ? (
        <button
          type="button"
          onClick={onPrimaryClick}
          className="inline-flex h-9 shrink-0 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
        >
          {primaryMode === "upload" ? <UploadIcon className="size-3.5" aria-hidden /> : null}
          {primaryMode === "plus" ? (
            <CollegeAdminPlusActionLabel iconClassName="size-3.5" label={primaryLabel} />
          ) : (
            primaryLabel
          )}
        </button>
      ) : null}
    </div>
  );
}