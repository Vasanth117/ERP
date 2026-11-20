import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function FastForwardIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M13 19L22 12L13 5V19Z"/>
      <path d="M2 19L11 12L2 5V19Z"/>

    </svg>
  );
}
