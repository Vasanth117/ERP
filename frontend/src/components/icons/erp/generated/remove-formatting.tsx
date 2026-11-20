import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function RemoveFormattingIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M4 7V4H20V7"/>
      <path d="M5 20H11"/>
      <path d="M13 4L8 20"/>
      <path d="M15 15L20 20"/>
      <path d="M20 15L15 20"/>

    </svg>
  );
}
