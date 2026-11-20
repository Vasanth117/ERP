import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ApertureIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M14.31 8L20.05 17.94"/>
      <path d="M9.69 8H21.17"/>
      <path d="M7.38 11.9996L13.12 2.05957"/>
      <path d="M9.69 15.9996L3.95 6.05957"/>
      <path d="M14.31 16H2.83"/>
      <path d="M16.62 12L10.88 21.94"/>

    </svg>
  );
}
