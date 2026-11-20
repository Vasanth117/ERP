import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function IndianRupeeIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M6 3H18"/>
      <path d="M6 8H18"/>
      <path d="M6 13L14.5 21"/>
      <path d="M6 13H9"/>
      <path d="M9 13C15.667 13 15.667 3 9 3"/>

    </svg>
  );
}
