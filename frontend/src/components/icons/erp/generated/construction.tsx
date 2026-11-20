import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ConstructionIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M3 6H21C21.2652 6 21.5196 6.10536 21.7071 6.29289C21.8946 6.48043 22 6.73478 22 7V13C22 13.2652 21.8946 13.5196 21.7071 13.7071C21.5196 13.8946 21.2652 14 21 14H3C2.73478 14 2.48043 13.8946 2.29289 13.7071C2.10536 13.5196 2 13.2652 2 13V7C2 6.73478 2.10536 6.48043 2.29289 6.29289C2.48043 6.10536 2.73478 6 3 6Z"/>
      <path d="M17 14V21"/>
      <path d="M7 14V21"/>
      <path d="M17 3V6"/>
      <path d="M7 3V6"/>
      <path d="M9.99999 13.9998L2.29999 6.2998"/>
      <path d="M14 6L21.7 13.7"/>
      <path d="M8 6L16 14"/>

    </svg>
  );
}
