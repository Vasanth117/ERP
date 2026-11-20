import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function DnaIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M10 16L11.5 17.5"/>
      <path d="M14 8L12.5 6.5"/>
      <path d="M15 2C13.202 3.998 12.482 5.995 12.193 7.993"/>
      <path d="M16.5 10.5L17.5 11.5"/>
      <path d="M17 6.00038L14.109 3.10938"/>
      <path d="M2 15C8.667 9 15.333 15 22 9"/>
      <path d="M20 9L20.891 9.891"/>
      <path d="M3.10901 14.1094L4.00001 15.0004"/>
      <path d="M6.5 12.5L7.5 13.5"/>
      <path d="M7 18L9.891 20.891"/>
      <path d="M9 21.9998C10.798 20.0018 11.518 18.0048 11.807 16.0068"/>

    </svg>
  );
}
