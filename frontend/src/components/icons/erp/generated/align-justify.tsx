import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function AlignJustifyIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M3 12H21"/>
      <path d="M3 18H21"/>
      <path d="M3 6H21"/>

    </svg>
  );
}
