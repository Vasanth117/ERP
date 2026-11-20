import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ChevronsLeftIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M11 17L6 12L11 7"/>
      <path d="M18 17L13 12L18 7"/>

    </svg>
  );
}
