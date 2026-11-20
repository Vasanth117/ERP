import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function PlugIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M12 22V17"/>
      <path d="M9 8V2"/>
      <path d="M15 8V2"/>
      <path d="M18 8V13C18 14.0609 17.5786 15.0783 16.8284 15.8284C16.0783 16.5786 15.0609 17 14 17H10C8.93913 17 7.92172 16.5786 7.17157 15.8284C6.42143 15.0783 6 14.0609 6 13V8H18Z"/>

    </svg>
  );
}
