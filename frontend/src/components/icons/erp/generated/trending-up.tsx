import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function TrendingUpIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M22 7L13.5 15.5L8.5 10.5L2 17"/>
      <path d="M16 7H22V13"/>

    </svg>
  );
}
