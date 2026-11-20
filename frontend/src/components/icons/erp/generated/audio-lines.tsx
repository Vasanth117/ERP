import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function AudioLinesIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M2 10V13"/>
      <path d="M6 6V17"/>
      <path d="M10 3V21"/>
      <path d="M14 8V15"/>
      <path d="M18 5V18"/>
      <path d="M22 10V13"/>

    </svg>
  );
}
