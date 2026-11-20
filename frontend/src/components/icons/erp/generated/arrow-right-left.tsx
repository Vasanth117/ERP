import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ArrowRightLeftIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M16 3L20 7L16 11"/>
      <path d="M20 7H4"/>
      <path d="M8 21L4 17L8 13"/>
      <path d="M4 17H20"/>

    </svg>
  );
}
