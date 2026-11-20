import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function TentIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M3.5 21L14 3"/>
      <path d="M20.5 21L10 3"/>
      <path d="M15.5 21L12 15L8.5 21"/>
      <path d="M2 21H22"/>

    </svg>
  );
}
