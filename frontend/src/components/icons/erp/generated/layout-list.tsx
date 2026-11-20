import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function LayoutListIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M4 3H9C9.26522 3 9.51957 3.10536 9.70711 3.29289C9.89464 3.48043 10 3.73478 10 4V9C10 9.26522 9.89464 9.51957 9.70711 9.70711C9.51957 9.89464 9.26522 10 9 10H4C3.73478 10 3.48043 9.89464 3.29289 9.70711C3.10536 9.51957 3 9.26522 3 9V4C3 3.73478 3.10536 3.48043 3.29289 3.29289C3.48043 3.10536 3.73478 3 4 3Z"/>
      <path d="M4 14H9C9.26522 14 9.51957 14.1054 9.70711 14.2929C9.89464 14.4804 10 14.7348 10 15V20C10 20.2652 9.89464 20.5196 9.70711 20.7071C9.51957 20.8946 9.26522 21 9 21H4C3.73478 21 3.48043 20.8946 3.29289 20.7071C3.10536 20.5196 3 20.2652 3 20V15C3 14.7348 3.10536 14.4804 3.29289 14.2929C3.48043 14.1054 3.73478 14 4 14Z"/>
      <path d="M14 4H21"/>
      <path d="M14 9H21"/>
      <path d="M14 15H21"/>
      <path d="M14 20H21"/>

    </svg>
  );
}
