import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function Move3DIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M5 3V19H21"/>
      <path d="M5 19L11 13"/>
      <path d="M2 6L5 3L8 6"/>
      <path d="M18 16L21 19L18 22"/>

    </svg>
  );
}
