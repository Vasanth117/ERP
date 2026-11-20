import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function TrendingUpDownIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M14.828 14.8281L21 21.0001"/>
      <path d="M21 16V21H16"/>
      <path d="M21 3L12 12L8 8L2 14"/>
      <path d="M21 8V3H16"/>

    </svg>
  );
}
