import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function Navigation2OffIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M9.31 9.31006L5 21.0001L12 17.0001L19 21.0001L17.83 17.8301"/>
      <path d="M14.53 8.88L12 2L10.83 5.17"/>
      <path d="M2 2L22 22"/>

    </svg>
  );
}
