import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function HashIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M4 9H20"/>
      <path d="M4 15H20"/>
      <path d="M10 3L8 21"/>
      <path d="M16 3L14 21"/>

    </svg>
  );
}
