import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function RssIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M4 11C6.38695 11 8.67613 11.9482 10.364 13.636C12.0518 15.3239 13 17.6131 13 20"/>
      <path d="M4 4C8.24346 4 12.3131 5.68571 15.3137 8.68629C18.3143 11.6869 20 15.7565 20 20"/>
      <path d="M4 19C4 19.2652 4.10536 19.5196 4.29289 19.7071C4.48043 19.8946 4.73478 20 5 20C5.26522 20 5.51957 19.8946 5.70711 19.7071C5.89464 19.5196 6 19.2652 6 19C6 18.7348 5.89464 18.4804 5.70711 18.2929C5.51957 18.1054 5.26522 18 5 18C4.73478 18 4.48043 18.1054 4.29289 18.2929C4.10536 18.4804 4 18.7348 4 19Z"/>

    </svg>
  );
}
