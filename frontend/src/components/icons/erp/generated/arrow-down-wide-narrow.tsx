import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ArrowDownWideNarrowIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M3 16L7 20L11 16"/>
      <path d="M7 20V4"/>
      <path d="M11 4H21"/>
      <path d="M11 8H18"/>
      <path d="M11 12H15"/>

    </svg>
  );
}
