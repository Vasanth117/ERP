import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function SprayCanIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M3 3H3.01"/>
      <path d="M7 5H7.01"/>
      <path d="M11 7H11.01"/>
      <path d="M3 7H3.01"/>
      <path d="M7 9H7.01"/>
      <path d="M3 11H3.01"/>
      <path d="M15 5H19V9H15V5Z"/>
      <path d="M19 9L21 11V21C21 21.6 20.6 22 20 22H14C13.4 22 13 21.6 13 21V11L15 9"/>
      <path d="M13 14L21 12"/>
      <path d="M13 19L21 17"/>

    </svg>
  );
}
