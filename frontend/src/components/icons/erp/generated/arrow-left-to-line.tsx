import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ArrowLeftToLineIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M3 19V5"/>
      <path d="M13 6L7 12L13 18"/>
      <path d="M7 12H21"/>

    </svg>
  );
}
