import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function PiIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M9 4V20"/>
      <path d="M4 7C4 5.3 5.3 4 7 4H20"/>
      <path d="M18 20C16.3 20 15 18.7 15 17V4"/>

    </svg>
  );
}
