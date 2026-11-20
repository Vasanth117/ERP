import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function SplitIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M16 3H21V8"/>
      <path d="M8 3H3V8"/>
      <path d="M12 22V13.7C12.0057 13.1674 11.905 12.639 11.7037 12.1458C11.5025 11.6526 11.2047 11.2046 10.828 10.828L3 3"/>
      <path d="M15 9L21 3"/>

    </svg>
  );
}
