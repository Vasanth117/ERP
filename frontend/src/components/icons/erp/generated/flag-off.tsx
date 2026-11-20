import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function FlagOffIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M8 2C11 2 13 4 16 4C19 4 20 3 20 3V14"/>
      <path d="M4 22V4"/>
      <path d="M4 15C4 15 5 14 8 14C11 14 13 16 16 16"/>
      <path d="M2 2L22 22"/>

    </svg>
  );
}
