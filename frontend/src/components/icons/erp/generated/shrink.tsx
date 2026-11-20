import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ShrinkIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M15 15L21 21M19.8 15H15V19.8"/>
      <path d="M4.2 15H9V19.8M9 15L3 21"/>
      <path d="M19.8 9H15V4.2M15 9L21 3"/>
      <path d="M4.2 9H9V4.2M9 9L3 3"/>

    </svg>
  );
}
