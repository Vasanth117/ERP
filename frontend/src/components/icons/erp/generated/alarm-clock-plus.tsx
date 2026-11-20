import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function AlarmClockPlusIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M4 13C4 15.1217 4.84285 17.1566 6.34315 18.6569C7.84344 20.1571 9.87827 21 12 21C14.1217 21 16.1566 20.1571 17.6569 18.6569C19.1571 17.1566 20 15.1217 20 13C20 10.8783 19.1571 8.84344 17.6569 7.34315C16.1566 5.84285 14.1217 5 12 5C9.87827 5 7.84344 5.84285 6.34315 7.34315C4.84285 8.84344 4 10.8783 4 13Z"/>
      <path d="M5 3L2 6"/>
      <path d="M22 6L19 3"/>
      <path d="M6.38 18.7002L4 21.0002"/>
      <path d="M17.64 18.6699L20 20.9999"/>
      <path d="M12 10V16"/>
      <path d="M9 13H15"/>

    </svg>
  );
}
