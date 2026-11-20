import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function CheckCheckIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M18 6L7 17L2 12"/>
      <path d="M22 10L14.5 17.5L13 16"/>

    </svg>
  );
}
