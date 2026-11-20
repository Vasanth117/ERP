import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ChevronsLeftRightIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M9 7L4 12L9 17"/>
      <path d="M15 7L20 12L15 17"/>

    </svg>
  );
}
