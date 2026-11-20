import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function FenceIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M4 3L2 5V20C2 20.6 2.4 21 3 21H5C5.6 21 6 20.6 6 20V5L4 3Z"/>
      <path d="M6 8H10"/>
      <path d="M6 18H10"/>
      <path d="M12 3L10 5V20C10 20.6 10.4 21 11 21H13C13.6 21 14 20.6 14 20V5L12 3Z"/>
      <path d="M14 8H18"/>
      <path d="M14 18H18"/>
      <path d="M20 3L18 5V20C18 20.6 18.4 21 19 21H21C21.6 21 22 20.6 22 20V5L20 3Z"/>

    </svg>
  );
}
