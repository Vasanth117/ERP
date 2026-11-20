import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function StarOffIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M8.34 8.33984L2 9.26984L7 14.1398L5.82 20.9998L12 17.7698L18.18 20.9998L17.59 17.5698"/>
      <path d="M18.4201 12.76L22.0001 9.27L15.0901 8.27L12.0001 2L10.5601 4.91"/>
      <path d="M2 2L22 22"/>

    </svg>
  );
}
