import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function UsbIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M9 7C9 7.26522 9.10536 7.51957 9.29289 7.70711C9.48043 7.89464 9.73478 8 10 8C10.2652 8 10.5196 7.89464 10.7071 7.70711C10.8946 7.51957 11 7.26522 11 7C11 6.73478 10.8946 6.48043 10.7071 6.29289C10.5196 6.10536 10.2652 6 10 6C9.73478 6 9.48043 6.10536 9.29289 6.29289C9.10536 6.48043 9 6.73478 9 7Z"/>
      <path d="M3 20C3 20.2652 3.10536 20.5196 3.29289 20.7071C3.48043 20.8946 3.73478 21 4 21C4.26522 21 4.51957 20.8946 4.70711 20.7071C4.89464 20.5196 5 20.2652 5 20C5 19.7348 4.89464 19.4804 4.70711 19.2929C4.51957 19.1054 4.26522 19 4 19C3.73478 19 3.48043 19.1054 3.29289 19.2929C3.10536 19.4804 3 19.7348 3 20Z"/>
      <path d="M4.70001 19.3L19 5"/>
      <path d="M21 3L18 4L20 6L21 3Z"/>
      <path d="M9.26 7.68018L5 12.0002L7 17.0002"/>
      <path d="M10 14L15 16L18.5 12.5"/>
      <path d="M18 12L19 11L20 12L19 13L18 12Z"/>

    </svg>
  );
}
