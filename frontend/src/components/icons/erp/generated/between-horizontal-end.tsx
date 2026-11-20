import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function BetweenHorizontalEndIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M4 3H15C15.2652 3 15.5196 3.10536 15.7071 3.29289C15.8946 3.48043 16 3.73478 16 4V9C16 9.26522 15.8946 9.51957 15.7071 9.70711C15.5196 9.89464 15.2652 10 15 10H4C3.73478 10 3.48043 9.89464 3.29289 9.70711C3.10536 9.51957 3 9.26522 3 9V4C3 3.73478 3.10536 3.48043 3.29289 3.29289C3.48043 3.10536 3.73478 3 4 3Z"/>
      <path d="M22 15L19 12L22 9"/>
      <path d="M4 14H15C15.2652 14 15.5196 14.1054 15.7071 14.2929C15.8946 14.4804 16 14.7348 16 15V20C16 20.2652 15.8946 20.5196 15.7071 20.7071C15.5196 20.8946 15.2652 21 15 21H4C3.73478 21 3.48043 20.8946 3.29289 20.7071C3.10536 20.5196 3 20.2652 3 20V15C3 14.7348 3.10536 14.4804 3.29289 14.2929C3.48043 14.1054 3.73478 14 4 14Z"/>

    </svg>
  );
}
