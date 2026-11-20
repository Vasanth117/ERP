import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function BellMinusIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M18.4 12C19.2 15.8 21 17 21 17H3C3 17 6 15 6 8C6 4.7 8.7 2 12 2C13.8 2 15.4 2.8 16.5 4"/>
      <path d="M10.3 21C10.4674 21.3044 10.7134 21.5583 11.0125 21.7352C11.3115 21.912 11.6526 22.0053 12 22.0053C12.3474 22.0053 12.6885 21.912 12.9875 21.7352C13.2865 21.5583 13.5326 21.3044 13.7 21"/>
      <path d="M15 8H21"/>

    </svg>
  );
}
