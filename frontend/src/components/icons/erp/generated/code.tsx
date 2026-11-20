import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function CodeIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M16 18L22 12L16 6"/>
      <path d="M8 6L2 12L8 18"/>

    </svg>
  );
}
