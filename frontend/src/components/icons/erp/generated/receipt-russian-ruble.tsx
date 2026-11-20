import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ReceiptRussianRubleIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M8 15H13"/>
      <path d="M8 11H13C13.5304 11 14.0391 10.7893 14.4142 10.4142C14.7893 10.0391 15 9.53043 15 9C15 8.46957 14.7893 7.96086 14.4142 7.58579C14.0391 7.21071 13.5304 7 13 7H10V17"/>

    </svg>
  );
}
