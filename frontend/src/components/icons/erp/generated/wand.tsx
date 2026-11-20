import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function WandIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M15 4V2"/>
      <path d="M15 16V14"/>
      <path d="M8 9H10"/>
      <path d="M20 9H22"/>
      <path d="M17.8 11.7998L19 12.9998"/>
      <path d="M15 9H15.01"/>
      <path d="M17.8 6.2L19 5"/>
      <path d="M3 21L12 12"/>
      <path d="M12.2 6.2L11 5"/>

    </svg>
  );
}
