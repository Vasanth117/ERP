import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ALargeSmallIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M21 14H16"/>
      <path d="M16 16V12.5C16 11.837 16.2634 11.2011 16.7322 10.7322C17.2011 10.2634 17.837 10 18.5 10C19.163 10 19.7989 10.2634 20.2678 10.7322C20.7366 11.2011 21 11.837 21 12.5V16"/>
      <path d="M4.5 13H10.5"/>
      <path d="M3 16L7.5 7L12 16"/>

    </svg>
  );
}
