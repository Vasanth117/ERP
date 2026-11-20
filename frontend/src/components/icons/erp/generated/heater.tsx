import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function HeaterIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M11 8C13 5 9 5 11 2"/>
      <path d="M15.5 8C17.5 5 13.5 5 15.5 2"/>
      <path d="M6 10H6.01"/>
      <path d="M6 14H6.01"/>
      <path d="M10 16V12"/>
      <path d="M14 16V12"/>
      <path d="M18 16V12"/>
      <path d="M20 6C20.5304 6 21.0391 6.21071 21.4142 6.58579C21.7893 6.96086 22 7.46957 22 8V18C22 18.5304 21.7893 19.0391 21.4142 19.4142C21.0391 19.7893 20.5304 20 20 20H4C3.46957 20 2.96086 19.7893 2.58579 19.4142C2.21071 19.0391 2 18.5304 2 18V8C2 7.46957 2.21071 6.96086 2.58579 6.58579C2.96086 6.21071 3.46957 6 4 6H7"/>
      <path d="M5 20V22"/>
      <path d="M19 20V22"/>

    </svg>
  );
}
