import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function EqualApproximatelyIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M5 15.0003C6.04519 14.3324 7.25964 13.9775 8.5 13.9775C9.74036 13.9775 10.9548 14.3324 12 15.0003C13.0452 15.6682 14.2596 16.0231 15.5 16.0231C16.7404 16.0231 17.9548 15.6682 19 15.0003"/>
      <path d="M5 9.00031C6.04519 8.33243 7.25964 7.97754 8.5 7.97754C9.74036 7.97754 10.9548 8.33243 12 9.00031C13.0452 9.6682 14.2596 10.0231 15.5 10.0231C16.7404 10.0231 17.9548 9.6682 19 9.00031"/>

    </svg>
  );
}
