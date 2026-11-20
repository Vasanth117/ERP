import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function HourglassIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M5 22H19"/>
      <path d="M5 2H19"/>
      <path d="M17 22V17.828C16.9999 17.2976 16.7891 16.789 16.414 16.414L12 12L7.586 16.414C7.2109 16.789 7.00011 17.2976 7 17.828V22"/>
      <path d="M7 2V6.172C7.00011 6.70239 7.2109 7.21101 7.586 7.586L12 12L16.414 7.586C16.7891 7.21101 16.9999 6.70239 17 6.172V2"/>

    </svg>
  );
}
