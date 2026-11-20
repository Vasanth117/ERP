import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function DribbbleIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M2 12C2 14.6522 3.05357 17.1957 4.92893 19.0711C6.8043 20.9464 9.34784 22 12 22C14.6522 22 17.1957 20.9464 19.0711 19.0711C20.9464 17.1957 22 14.6522 22 12C22 9.34784 20.9464 6.8043 19.0711 4.92893C17.1957 3.05357 14.6522 2 12 2C9.34784 2 6.8043 3.05357 4.92893 4.92893C3.05357 6.8043 2 9.34784 2 12Z"/>
      <path d="M19.13 5.08984C15.22 9.13984 10 10.4398 2.25 10.9398"/>
      <path d="M21.75 12.8396C15.13 11.4296 9.60999 13.8396 5.37 19.1596"/>
      <path d="M8.56 2.75C12.93 8.75 14.56 12.17 16.56 20.47"/>

    </svg>
  );
}
