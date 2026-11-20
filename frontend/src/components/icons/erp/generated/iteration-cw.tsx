import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function IterationCwIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M4 10C4 5.6 7.6 2 12 2C16.4 2 20 5.6 20 10C20 14.4 16.4 18 12 18H4"/>
      <path d="M8 22L4 18L8 14"/>

    </svg>
  );
}
