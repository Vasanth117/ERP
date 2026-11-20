import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ExpandIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M21 21L15 15M16.2 21H21V16.2"/>
      <path d="M7.8 21H3V16.2M3 21L9 15"/>
      <path d="M16.2 3H21V7.8M21 3L15 9"/>
      <path d="M7.8 3H3V7.8M3 3L9 9"/>

    </svg>
  );
}
