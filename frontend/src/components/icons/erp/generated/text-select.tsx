import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function TextSelectIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M5 3C4.46957 3 3.96086 3.21071 3.58579 3.58579C3.21071 3.96086 3 4.46957 3 5"/>
      <path d="M19 3C19.5304 3 20.0391 3.21071 20.4142 3.58579C20.7893 3.96086 21 4.46957 21 5"/>
      <path d="M21 19C21 19.5304 20.7893 20.0391 20.4142 20.4142C20.0391 20.7893 19.5304 21 19 21"/>
      <path d="M5 21C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19"/>
      <path d="M9 3H10"/>
      <path d="M9 21H10"/>
      <path d="M14 3H15"/>
      <path d="M14 21H15"/>
      <path d="M3 9V10"/>
      <path d="M21 9V10"/>
      <path d="M3 14V15"/>
      <path d="M21 14V15"/>
      <path d="M7 8H15"/>
      <path d="M7 12H17"/>
      <path d="M7 16H13"/>

    </svg>
  );
}
