import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function TimerIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M10 2H14"/>
      <path d="M12 14L15 11"/>
      <path d="M4 14C4 16.1217 4.84285 18.1566 6.34315 19.6569C7.84344 21.1571 9.87827 22 12 22C14.1217 22 16.1566 21.1571 17.6569 19.6569C19.1571 18.1566 20 16.1217 20 14C20 11.8783 19.1571 9.84344 17.6569 8.34315C16.1566 6.84285 14.1217 6 12 6C9.87827 6 7.84344 6.84285 6.34315 8.34315C4.84285 9.84344 4 11.8783 4 14Z"/>

    </svg>
  );
}
