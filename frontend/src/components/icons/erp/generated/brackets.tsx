import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function BracketsIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M16 3H19V21H16"/>
      <path d="M8 21H5V3H8"/>

    </svg>
  );
}
