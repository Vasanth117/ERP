import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function UtensilsCrossedIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M16 2L13.7 4.3C13.1503 4.86079 12.8424 5.61474 12.8424 6.4C12.8424 7.18526 13.1503 7.93921 13.7 8.5L15.5 10.3C16.0608 10.8497 16.8147 11.1576 17.6 11.1576C18.3852 11.1576 19.1392 10.8497 19.7 10.3L22 8"/>
      <path d="M15 14.9998L3.30001 3.2998C2.90089 3.69086 2.58382 4.15762 2.36736 4.67276C2.15089 5.18789 2.0394 5.74104 2.0394 6.2998C2.0394 6.85857 2.15089 7.41172 2.36736 7.92685C2.58382 8.44199 2.90089 8.90875 3.30001 9.2998L10.6 16.5998C11.3 17.2998 12.6 17.2998 13.4 16.5998L15 14.9998ZM15 14.9998L22 21.9998"/>
      <path d="M2.10001 21.8L8.50001 15.5"/>
      <path d="M19 5L12 12"/>

    </svg>
  );
}
