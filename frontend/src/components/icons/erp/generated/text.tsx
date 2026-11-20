import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function TextIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M17 6.1001H3"/>
      <path d="M21 12.1001H3"/>
      <path d="M15.1 18H3"/>

    </svg>
  );
}
