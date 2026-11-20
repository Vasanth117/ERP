import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function AntennaIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M2 12L7 2"/>
      <path d="M7 12L12 2"/>
      <path d="M12 12L17 2"/>
      <path d="M17 12L22 2"/>
      <path d="M4.5 7H19.5"/>
      <path d="M12 16V22"/>

    </svg>
  );
}
