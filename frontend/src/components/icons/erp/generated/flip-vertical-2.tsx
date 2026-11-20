import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function FlipVertical2Icon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M17 3L12 8L7 3H17Z"/>
      <path d="M17 21L12 16L7 21H17Z"/>
      <path d="M4 12H2"/>
      <path d="M10 12H8"/>
      <path d="M16 12H14"/>
      <path d="M22 12H20"/>

    </svg>
  );
}
