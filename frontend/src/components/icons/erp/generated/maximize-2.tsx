import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function Maximize2Icon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M15 3H21V9"/>
      <path d="M9 21H3V15"/>
      <path d="M21 3L14 10"/>
      <path d="M3 21L10 14"/>

    </svg>
  );
}
