import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ChevronsRightLeftIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M20 17L15 12L20 7"/>
      <path d="M4 17L9 12L4 7"/>

    </svg>
  );
}
