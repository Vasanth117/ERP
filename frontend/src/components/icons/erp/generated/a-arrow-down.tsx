import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function AArrowDownIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={cn("size-6 shrink-0", className)}
      aria-hidden
      {...props}
    >
      <path d="M3.5 13H9.5"/>
      <path d="M2 16L6.5 7L11 16"/>
      <path d="M18 7V16"/>
      <path d="M14 12L18 16L22 12"/>

    </svg>
  );
}
