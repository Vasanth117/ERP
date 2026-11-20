import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ConciergeBellIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M3 20C2.73478 20 2.48043 19.8946 2.29289 19.7071C2.10536 19.5196 2 19.2652 2 19V18C2 17.4696 2.21071 16.9609 2.58579 16.5858C2.96086 16.2107 3.46957 16 4 16H20C20.5304 16 21.0391 16.2107 21.4142 16.5858C21.7893 16.9609 22 17.4696 22 18V19C22 19.2652 21.8946 19.5196 21.7071 19.7071C21.5196 19.8946 21.2652 20 21 20H3Z"/>
      <path d="M20 16C20 13.8783 19.1571 11.8434 17.6569 10.3431C16.1566 8.84285 14.1217 8 12 8C9.87827 8 7.84344 8.84285 6.34315 10.3431C4.84285 11.8434 4 13.8783 4 16"/>
      <path d="M12 4V8"/>
      <path d="M10 4H14"/>

    </svg>
  );
}
