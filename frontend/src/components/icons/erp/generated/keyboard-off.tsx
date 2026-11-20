import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function KeyboardOffIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M20 4C20.5304 4 21.0391 4.21071 21.4142 4.58579C21.7893 4.96086 22 5.46957 22 6"/>
      <path d="M22 6V16.41"/>
      <path d="M7 16H16"/>
      <path d="M9.69 4H20"/>
      <path d="M14 8H14.01"/>
      <path d="M18 8H18.01"/>
      <path d="M2 2L22 22"/>
      <path d="M20 20H4C3.46957 20 2.96086 19.7893 2.58579 19.4142C2.21071 19.0391 2 18.5304 2 18V6C2 5.46957 2.21071 4.96086 2.58579 4.58579C2.96086 4.21071 3.46957 4 4 4"/>
      <path d="M6 8H6.01"/>
      <path d="M8 12H8.01"/>

    </svg>
  );
}
