import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function UndoIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M3 7V13H9"/>
      <path d="M21 17C21 14.6131 20.0518 12.3239 18.364 10.636C16.6761 8.94821 14.3869 8 12 8C9.78512 8.00226 7.64885 8.82116 6 10.3L3 13"/>

    </svg>
  );
}
