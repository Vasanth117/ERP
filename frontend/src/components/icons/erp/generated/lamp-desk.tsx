import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function LampDeskIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M14 5L11 8L13 15L21 7L14 5Z"/>
      <path d="M14 5L11 8L8 5L11 2L14 5Z"/>
      <path d="M9.5 6.5L4 12L7 18"/>
      <path d="M3 22V20C3 18.9 3.9 18 5 18H9C9.53043 18 10.0391 18.2107 10.4142 18.5858C10.7893 18.9609 11 19.4696 11 20V22H3Z"/>

    </svg>
  );
}
