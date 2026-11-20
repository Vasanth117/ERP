import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function RefreshCwOffIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M21 8L18.74 5.74C16.931 3.99122 14.5161 3.00947 12 3C11 3 10.03 3.16 9.13 3.47"/>
      <path d="M8 16H3V21"/>
      <path d="M3 11.9996C3 9.50965 4 7.25965 5.64 5.63965"/>
      <path d="M3 16L5.26 18.26C7.06897 20.0088 9.48395 20.9905 12 21C14.49 21 16.74 20 18.36 18.36"/>
      <path d="M21 12C21 13 20.84 13.97 20.53 14.87"/>
      <path d="M21 3V8H16"/>
      <path d="M22 22L2 2"/>

    </svg>
  );
}
