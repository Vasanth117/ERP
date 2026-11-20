import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function Heading5Icon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M4 12H12"/>
      <path d="M4 18V6"/>
      <path d="M12 18V6"/>
      <path d="M17 13V10H21"/>
      <path d="M17 17.7C17.4 17.9 17.8 18 18.3 18C19.8 18 21 16.9 21 15.5C21 14.1 19.8 13 18.3 13H17"/>

    </svg>
  );
}
