import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function VibrateOffIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M2 8L4 10L2 12L4 14L2 16"/>
      <path d="M22 8L20 10L22 12L20 14L22 16"/>
      <path d="M8 8V18C8 18.55 8.45 19 9 19H15C15.55 19 16 18.55 16 18V16"/>
      <path d="M16 10.34V6C16 5.45 15.55 5 15 5H10.66"/>
      <path d="M2 2L22 22"/>

    </svg>
  );
}
