import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function BarcodeIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M3 5V19"/>
      <path d="M8 5V19"/>
      <path d="M12 5V19"/>
      <path d="M17 5V19"/>
      <path d="M21 5V19"/>

    </svg>
  );
}
