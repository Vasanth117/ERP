import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function Minimize2Icon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M4 14H10V20"/>
      <path d="M20 10H14V4"/>
      <path d="M14 10L21 3"/>
      <path d="M3 21L10 14"/>

    </svg>
  );
}
