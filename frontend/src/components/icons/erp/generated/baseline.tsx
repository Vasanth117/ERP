import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function BaselineIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M4 20H20"/>
      <path d="M6 16L12 4L18 16"/>
      <path d="M8 12H16"/>

    </svg>
  );
}
