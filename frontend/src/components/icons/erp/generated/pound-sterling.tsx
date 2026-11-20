import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function PoundSterlingIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M18 6.99999C18 1.66699 10 1.66699 10 6.99999"/>
      <path d="M10 7V21"/>
      <path d="M6 21H18"/>
      <path d="M6 13H16"/>

    </svg>
  );
}
