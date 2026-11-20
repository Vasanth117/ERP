import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function TestTubesIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M9 2V19.5C9 20.163 8.73661 20.7989 8.26777 21.2678C7.79893 21.7366 7.16304 22 6.5 22C5.83696 22 5.20107 21.7366 4.73223 21.2678C4.26339 20.7989 4 20.163 4 19.5V2"/>
      <path d="M20 2V19.5C20 20.163 19.7366 20.7989 19.2678 21.2678C18.7989 21.7366 18.163 22 17.5 22C16.837 22 16.2011 21.7366 15.7322 21.2678C15.2634 20.7989 15 20.163 15 19.5V2"/>
      <path d="M3 2H10"/>
      <path d="M14 2H21"/>
      <path d="M9 16H4"/>
      <path d="M20 16H15"/>

    </svg>
  );
}
