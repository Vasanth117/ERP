import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function TextQuoteIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M17 6H3"/>
      <path d="M21 12H8"/>
      <path d="M21 18H8"/>
      <path d="M3 12V18"/>

    </svg>
  );
}
