import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function SwordIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M14.5 17.5L3 6V3H6L17.5 14.5"/>
      <path d="M13 19L19 13"/>
      <path d="M16 16L20 20"/>
      <path d="M19 21L21 19"/>

    </svg>
  );
}
