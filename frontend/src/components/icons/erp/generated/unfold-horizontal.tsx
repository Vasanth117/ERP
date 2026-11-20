import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function UnfoldHorizontalIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M16 12H22"/>
      <path d="M8 12H2"/>
      <path d="M12 2V4"/>
      <path d="M12 8V10"/>
      <path d="M12 14V16"/>
      <path d="M12 20V22"/>
      <path d="M19 15L22 12L19 9"/>
      <path d="M5 9L2 12L5 15"/>

    </svg>
  );
}
