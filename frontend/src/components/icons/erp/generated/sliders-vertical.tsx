import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function SlidersVerticalIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M4 21V14"/>
      <path d="M4 10V3"/>
      <path d="M12 21V12"/>
      <path d="M12 8V3"/>
      <path d="M20 21V16"/>
      <path d="M20 12V3"/>
      <path d="M2 14H6"/>
      <path d="M10 8H14"/>
      <path d="M18 16H22"/>

    </svg>
  );
}
