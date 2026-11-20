import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ParenthesesIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M8 21C8 21 4 18 4 12C4 6 8 3 8 3"/>
      <path d="M16 3C16 3 20 6 20 12C20 18 16 21 16 21"/>

    </svg>
  );
}
