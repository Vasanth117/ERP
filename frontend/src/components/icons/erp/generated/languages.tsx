import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function LanguagesIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M5 8L11 14"/>
      <path d="M4 14L10 8L12 5"/>
      <path d="M2 5H14"/>
      <path d="M7 2H8"/>
      <path d="M22 22L17 12L12 22"/>
      <path d="M14 18H20"/>

    </svg>
  );
}
