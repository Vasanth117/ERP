import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ArrowLeftRightIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M8 3L4 7L8 11"/>
      <path d="M4 7H20"/>
      <path d="M16 21L20 17L16 13"/>
      <path d="M20 17H4"/>

    </svg>
  );
}
