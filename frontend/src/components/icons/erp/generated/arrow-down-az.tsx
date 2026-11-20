import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ArrowDownAzIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M3 16L7 20L11 16"/>
      <path d="M7 20V4"/>
      <path d="M20 8H15"/>
      <path d="M15 10V6.5C15 5.83696 15.2634 5.20107 15.7322 4.73223C16.2011 4.26339 16.837 4 17.5 4C18.163 4 18.7989 4.26339 19.2678 4.73223C19.7366 5.20107 20 5.83696 20 6.5V10"/>
      <path d="M15 14H20L15 20H20"/>

    </svg>
  );
}
