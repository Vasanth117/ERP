import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function MoveIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M12 2V22"/>
      <path d="M15 19L12 22L9 19"/>
      <path d="M19 9L22 12L19 15"/>
      <path d="M2 12H22"/>
      <path d="M5 9L2 12L5 15"/>
      <path d="M9 5L12 2L15 5"/>

    </svg>
  );
}
