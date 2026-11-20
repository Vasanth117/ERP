import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function UtilityPoleIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M12 2V22"/>
      <path d="M2 5H22"/>
      <path d="M3 3V5"/>
      <path d="M7 3V5"/>
      <path d="M17 3V5"/>
      <path d="M21 3V5"/>
      <path d="M19 5L12 12L5 5"/>

    </svg>
  );
}
