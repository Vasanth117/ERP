import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function PiggyBankIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M19 5C17.5 5 16.2 6.4 16 7C12.5 5.5 5 6.7 5 12C5 13.8 5 15 7 16.5V20H11V18H14V20H18V16C19 15.5 19.7 15 20 14H22V10H20C20 9 19.5 8.5 19 8V5Z"/>
      <path d="M2 9V10C2 11.1 2.9 12 4 12H5"/>
      <path d="M16 11H16.01"/>

    </svg>
  );
}
