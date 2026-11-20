import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function LigatureIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M8 20V8C8 5.8 9.8 4 12 4C13.5 4 14.8 4.8 15.5 6"/>
      <path d="M6 12H10"/>
      <path d="M14 12H16V20"/>
      <path d="M6 20H10"/>
      <path d="M14 20H18"/>

    </svg>
  );
}
