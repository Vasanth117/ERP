import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function BetweenVerticalEndIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M4 3H9C9.26522 3 9.51957 3.10536 9.70711 3.29289C9.89464 3.48043 10 3.73478 10 4V15C10 15.2652 9.89464 15.5196 9.70711 15.7071C9.51957 15.8946 9.26522 16 9 16H4C3.73478 16 3.48043 15.8946 3.29289 15.7071C3.10536 15.5196 3 15.2652 3 15V4C3 3.73478 3.10536 3.48043 3.29289 3.29289C3.48043 3.10536 3.73478 3 4 3Z"/>
      <path d="M9 22L12 19L15 22"/>
      <path d="M15 3H20C20.2652 3 20.5196 3.10536 20.7071 3.29289C20.8946 3.48043 21 3.73478 21 4V15C21 15.2652 20.8946 15.5196 20.7071 15.7071C20.5196 15.8946 20.2652 16 20 16H15C14.7348 16 14.4804 15.8946 14.2929 15.7071C14.1054 15.5196 14 15.2652 14 15V4C14 3.73478 14.1054 3.48043 14.2929 3.29289C14.4804 3.10536 14.7348 3 15 3Z"/>

    </svg>
  );
}
