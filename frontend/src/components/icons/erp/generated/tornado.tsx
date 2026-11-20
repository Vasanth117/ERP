import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function TornadoIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M21 4H3"/>
      <path d="M18 8H6"/>
      <path d="M19 12H9"/>
      <path d="M16 16H10"/>
      <path d="M11 20H9"/>

    </svg>
  );
}
