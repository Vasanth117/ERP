import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function LetterTextIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M15 12H21"/>
      <path d="M15 6H21"/>
      <path d="M3 13L6.553 5.27597C6.59457 5.19303 6.6584 5.12329 6.73734 5.07455C6.81628 5.02581 6.90723 5 7 5C7.09277 5 7.18372 5.02581 7.26266 5.07455C7.3416 5.12329 7.40543 5.19303 7.447 5.27597L11 13"/>
      <path d="M3 18H21"/>
      <path d="M4 11H10"/>

    </svg>
  );
}
