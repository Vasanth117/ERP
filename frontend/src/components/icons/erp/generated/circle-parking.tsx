import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function CircleParkingIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M9 17V7H13C13.7956 7 14.5587 7.31607 15.1213 7.87868C15.6839 8.44129 16 9.20435 16 10C16 10.7956 15.6839 11.5587 15.1213 12.1213C14.5587 12.6839 13.7956 13 13 13H9"/>

    </svg>
  );
}
