import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function LampFloorIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M9 2H15L18 9H6L9 2Z"/>
      <path d="M12 9V22"/>
      <path d="M9 22H15"/>

    </svg>
  );
}
