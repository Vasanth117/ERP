import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function IndentIncreaseIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M21 12H11"/>
      <path d="M21 18H11"/>
      <path d="M21 6H11"/>
      <path d="M3 8L7 12L3 16"/>

    </svg>
  );
}
