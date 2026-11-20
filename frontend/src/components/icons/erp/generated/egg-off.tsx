import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function EggOffIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M6.39904 6.39941C5.36204 8.15741 4.65004 10.1894 4.50004 12.0004C4.13004 16.4304 5.77004 21.9504 12 22.0004C15.256 21.9744 17.259 20.4534 18.375 18.3754"/>
      <path d="M19.532 13.875C19.563 13.25 19.5523 12.6236 19.5 12C19.14 7.66 15.55 2.04 12 2C10.96 2.012 9.91798 2.502 8.95398 3.297"/>
      <path d="M2 2L22 22"/>

    </svg>
  );
}
