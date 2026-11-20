import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ChevronLastIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M7 18L13 12L7 6"/>
      <path d="M17 6V18"/>

    </svg>
  );
}
