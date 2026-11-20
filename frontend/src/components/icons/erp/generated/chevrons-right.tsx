import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ChevronsRightIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M6 17L11 12L6 7"/>
      <path d="M13 17L18 12L13 7"/>

    </svg>
  );
}
