import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function CigaretteIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M17 12H3C2.73478 12 2.48043 12.1054 2.29289 12.2929C2.10536 12.4804 2 12.7348 2 13V15C2 15.2652 2.10536 15.5196 2.29289 15.7071C2.48043 15.8946 2.73478 16 3 16H17"/>
      <path d="M18 8C18 5.5 16 5.5 16 3"/>
      <path d="M21 16C21.2652 16 21.5196 15.8946 21.7071 15.7071C21.8946 15.5196 22 15.2652 22 15V13C22 12.7348 21.8946 12.4804 21.7071 12.2929C21.5196 12.1054 21.2652 12 21 12"/>
      <path d="M22 8C22 5.5 20 5.5 20 3"/>
      <path d="M7 12V16"/>

    </svg>
  );
}
