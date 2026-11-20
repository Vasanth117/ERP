import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function GemIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M6 3H18L22 9L12 22L2 9L6 3Z"/>
      <path d="M11 3L8 9L12 22L16 9L13 3"/>
      <path d="M2 9H22"/>

    </svg>
  );
}
