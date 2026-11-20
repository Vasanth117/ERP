import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function VoteIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M9 12L11 14L15 10"/>
      <path d="M5 7C5 5.9 5.9 5 7 5H17C17.5304 5 18.0391 5.21071 18.4142 5.58579C18.7893 5.96086 19 6.46957 19 7V19H5V7Z"/>
      <path d="M22 19H2"/>

    </svg>
  );
}
