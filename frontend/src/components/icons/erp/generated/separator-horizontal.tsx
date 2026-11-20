import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function SeparatorHorizontalIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M3 12H21"/>
      <path d="M8 8L12 4L16 8"/>
      <path d="M16 16L12 20L8 16"/>

    </svg>
  );
}
