import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ListTreeIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M21 12H13"/>
      <path d="M21 6H8"/>
      <path d="M21 18H13"/>
      <path d="M3 6V10C3 11.1 3.9 12 5 12H8"/>
      <path d="M3 10V16C3 17.1 3.9 18 5 18H8"/>

    </svg>
  );
}
