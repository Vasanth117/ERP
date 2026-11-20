import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ListOrderedIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M10 12H21"/>
      <path d="M10 18H21"/>
      <path d="M10 6H21"/>
      <path d="M4 10H6"/>
      <path d="M4 6H5V10"/>
      <path d="M6 17.9999H4C4 16.9999 6 15.9999 6 14.9999C6 13.9999 5 13.4999 4 13.9999"/>

    </svg>
  );
}
