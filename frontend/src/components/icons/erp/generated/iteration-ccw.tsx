import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function IterationCcwIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M20 10C20 5.6 16.4 2 12 2C7.6 2 4 5.6 4 10C4 14.4 7.6 18 12 18H20"/>
      <path d="M16 14L20 18L16 22"/>

    </svg>
  );
}
