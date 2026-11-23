"use client";

import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

export const institutionActionFooterClassName = cn(
  "sticky bottom-0 z-10 -mx-6 -mb-5 mt-8 flex flex-col gap-3",
  "border-t border-[#e8ecf2] bg-[#f8fafc]/95 px-6 py-4 backdrop-blur",
  "sm:flex-row sm:items-center sm:justify-between",
  "md:-mx-8 md:-mb-6 md:px-8",
);

export const institutionActionButtonOutline =
  "h-9 min-w-[5.25rem] border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151]";

export const institutionActionButtonPrimary =
  "h-9 min-w-[7.5rem] gap-1.5 bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]";

type InstitutionPageActionFooterProps = {
  note?: ReactNode;
  children: ReactNode;
  className?: string;
};

export function InstitutionPageActionFooter({
  note,
  children,
  className,
}: InstitutionPageActionFooterProps) {
  return (
    <footer className={cn(institutionActionFooterClassName, className)}>
      {note ? (
        <p className="text-[11px] leading-relaxed text-[#9ca3af] sm:max-w-[55%]">{note}</p>
      ) : (
        <span className="hidden min-h-px sm:block sm:flex-1" aria-hidden />
      )}
      <div className="flex shrink-0 flex-wrap items-center justify-end gap-2">{children}</div>
    </footer>
  );
}