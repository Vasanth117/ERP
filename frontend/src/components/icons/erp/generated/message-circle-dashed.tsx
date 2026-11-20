import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function MessageCircleDashedIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M13.5 3.1C13 3.1 12.5 3 12 3C11.5 3 11 3.1 10.5 3.1"/>
      <path d="M19.3 6.79995C18.7035 6.00355 17.9964 5.29641 17.2 4.69995"/>
      <path d="M20.9 13.5C21 13 21 12.5 21 12C21 11.5 20.9 11 20.9 10.5"/>
      <path d="M17.2 19.2999C17.9964 18.7035 18.7035 17.9964 19.3 17.2"/>
      <path d="M10.5 20.8999C11 20.9999 11.5 20.9999 12 20.9999C12.5 20.9999 13 20.8999 13.5 20.8999"/>
      <path d="M3.5 17.5L2 22L6.5 20.5"/>
      <path d="M3.1 10.5C3.1 11 3 11.5 3 12C3 12.5 3.1 13 3.1 13.5"/>
      <path d="M6.8 4.69995C6.00359 5.29641 5.29645 6.00355 4.7 6.79995"/>

    </svg>
  );
}
