import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function HazeIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M5.19995 6.2002L6.59995 7.6002"/>
      <path d="M2 13H4"/>
      <path d="M20 13H22"/>
      <path d="M17.4 7.6002L18.8 6.2002"/>
      <path d="M22 17H2"/>
      <path d="M22 21H2"/>
      <path d="M16 13C16 11.9391 15.5786 10.9217 14.8284 10.1716C14.0783 9.42143 13.0609 9 12 9C10.9391 9 9.92172 9.42143 9.17157 10.1716C8.42143 10.9217 8 11.9391 8 13"/>
      <path d="M12 5V2.5"/>

    </svg>
  );
}
