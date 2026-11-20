import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ListCollapseIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M3 10L5.5 7.5L3 5"/>
      <path d="M3 19L5.5 16.5L3 14"/>
      <path d="M10 6H21"/>
      <path d="M10 12H21"/>
      <path d="M10 18H21"/>

    </svg>
  );
}
