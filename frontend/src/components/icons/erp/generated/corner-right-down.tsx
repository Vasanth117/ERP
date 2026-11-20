import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function CornerRightDownIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M10 15L15 20L20 15"/>
      <path d="M4 4H11C12.0609 4 13.0783 4.42143 13.8284 5.17157C14.5786 5.92172 15 6.93913 15 8V20"/>

    </svg>
  );
}
