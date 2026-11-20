import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function SunsetIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M12 10V2"/>
      <path d="M4.92999 10.9297L6.33999 12.3397"/>
      <path d="M2 18H4"/>
      <path d="M20 18H22"/>
      <path d="M19.07 10.9297L17.66 12.3397"/>
      <path d="M22 22H2"/>
      <path d="M16 6L12 10L8 6"/>
      <path d="M16 18C16 16.9391 15.5786 15.9217 14.8284 15.1716C14.0783 14.4214 13.0609 14 12 14C10.9391 14 9.92172 14.4214 9.17157 15.1716C8.42143 15.9217 8 16.9391 8 18"/>

    </svg>
  );
}
