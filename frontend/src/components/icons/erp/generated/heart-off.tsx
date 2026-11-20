import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function HeartOffIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M2 2L22 22"/>
      <path d="M16.5 16.5004L12 21.0004L5 14.0004C3.5 12.5504 2 10.8004 2 8.50039C2.00067 7.66001 2.1939 6.83096 2.56487 6.07689C2.93584 5.32282 3.47467 4.66379 4.14 4.15039"/>
      <path d="M8.76001 3.1C9.91001 3.32 10.89 3.88 12 5C13.5 3.5 14.74 3 16.5 3C17.9587 3 19.3576 3.57946 20.3891 4.61091C21.4205 5.64236 22 7.04131 22 8.5C22 10.62 20.7 12.28 19.33 13.67"/>

    </svg>
  );
}
