import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function BetweenHorizontalStartIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M9 3H20C20.2652 3 20.5196 3.10536 20.7071 3.29289C20.8946 3.48043 21 3.73478 21 4V9C21 9.26522 20.8946 9.51957 20.7071 9.70711C20.5196 9.89464 20.2652 10 20 10H9C8.73478 10 8.48043 9.89464 8.29289 9.70711C8.10536 9.51957 8 9.26522 8 9V4C8 3.73478 8.10536 3.48043 8.29289 3.29289C8.48043 3.10536 8.73478 3 9 3Z"/>
      <path d="M2 9L5 12L2 15"/>
      <path d="M9 14H20C20.2652 14 20.5196 14.1054 20.7071 14.2929C20.8946 14.4804 21 14.7348 21 15V20C21 20.2652 20.8946 20.5196 20.7071 20.7071C20.5196 20.8946 20.2652 21 20 21H9C8.73478 21 8.48043 20.8946 8.29289 20.7071C8.10536 20.5196 8 20.2652 8 20V15C8 14.7348 8.10536 14.4804 8.29289 14.2929C8.48043 14.1054 8.73478 14 9 14Z"/>

    </svg>
  );
}
