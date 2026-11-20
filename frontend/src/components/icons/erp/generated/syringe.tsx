import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function SyringeIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M18 2L22 6"/>
      <path d="M17 7L20 4"/>
      <path d="M19 9L8.70001 19.3C7.70001 20.3 6.20001 20.3 5.30001 19.3L4.70001 18.7C3.70001 17.7 3.70001 16.2 4.70001 15.3L15 5"/>
      <path d="M9 11L13 15"/>
      <path d="M5 19L2 22"/>
      <path d="M14 4L20 10"/>

    </svg>
  );
}
