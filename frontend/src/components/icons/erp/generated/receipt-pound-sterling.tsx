import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ReceiptPoundSterlingIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M4 2V22L6 21L8 22L10 21L12 22L14 21L16 22L18 21L20 22V2L18 3L16 2L14 3L12 2L10 3L8 2L6 3L4 2Z"/>
      <path d="M8 13H13"/>
      <path d="M10 17V9.5C10 8.83696 10.2634 8.20107 10.7322 7.73223C11.2011 7.26339 11.837 7 12.5 7C13.163 7 13.7989 7.26339 14.2678 7.73223C14.7366 8.20107 15 8.83696 15 9.5"/>
      <path d="M8 17H15"/>

    </svg>
  );
}
