import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ArrowUpWideNarrowIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M3 8L7 4L11 8"/>
      <path d="M7 4V20"/>
      <path d="M11 12H21"/>
      <path d="M11 16H18"/>
      <path d="M11 20H15"/>

    </svg>
  );
}
