import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function SquareSplitVerticalIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M5 8V5C5 4 6 3 7 3H17C18 3 19 4 19 5V8"/>
      <path d="M19 16V19C19 20 18 21 17 21H7C6 21 5 20 5 19V16"/>
      <path d="M4 12H20"/>

    </svg>
  );
}
