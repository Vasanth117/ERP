import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ArrowsUpFromLineIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M4 6L7 3L10 6"/>
      <path d="M7 17V3"/>
      <path d="M14 6L17 3L20 6"/>
      <path d="M17 17V3"/>
      <path d="M4 21H20"/>

    </svg>
  );
}
