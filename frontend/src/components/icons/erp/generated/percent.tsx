import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function PercentIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M19 5L5 19"/>
      <path d="M4 6.5C4 7.16304 4.26339 7.79893 4.73223 8.26777C5.20107 8.73661 5.83696 9 6.5 9C7.16304 9 7.79893 8.73661 8.26777 8.26777C8.73661 7.79893 9 7.16304 9 6.5C9 5.83696 8.73661 5.20107 8.26777 4.73223C7.79893 4.26339 7.16304 4 6.5 4C5.83696 4 5.20107 4.26339 4.73223 4.73223C4.26339 5.20107 4 5.83696 4 6.5Z"/>
      <path d="M15 17.5C15 18.163 15.2634 18.7989 15.7322 19.2678C16.2011 19.7366 16.837 20 17.5 20C18.163 20 18.7989 19.7366 19.2678 19.2678C19.7366 18.7989 20 18.163 20 17.5C20 16.837 19.7366 16.2011 19.2678 15.7322C18.7989 15.2634 18.163 15 17.5 15C16.837 15 16.2011 15.2634 15.7322 15.7322C15.2634 16.2011 15 16.837 15 17.5Z"/>

    </svg>
  );
}
