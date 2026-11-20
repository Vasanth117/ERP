import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function SkipForwardIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M5 4L15 12L5 20V4Z"/>
      <path d="M19 5V19"/>

    </svg>
  );
}
