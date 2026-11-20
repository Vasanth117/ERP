import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function NavigationOffIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M8.43 8.43018L3 11.0002L11 13.0002L13 21.0002L15.57 15.5702"/>
      <path d="M17.39 11.73L22 2L12.27 6.61"/>
      <path d="M2 2L22 22"/>

    </svg>
  );
}
