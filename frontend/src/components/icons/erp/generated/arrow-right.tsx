import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ArrowRightIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M5 12H19"/>
      <path d="M12 5L19 12L12 19"/>

    </svg>
  );
}
