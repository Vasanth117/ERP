import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function Repeat1Icon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M17 2L21 6L17 10"/>
      <path d="M3 11V10C3 8.93913 3.42143 7.92172 4.17157 7.17157C4.92172 6.42143 5.93913 6 7 6H21"/>
      <path d="M7 22L3 18L7 14"/>
      <path d="M21 13V14C21 15.0609 20.5786 16.0783 19.8284 16.8284C19.0783 17.5786 18.0609 18 17 18H3"/>
      <path d="M11 10H12V14"/>

    </svg>
  );
}
