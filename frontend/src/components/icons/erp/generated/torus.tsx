import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function TorusIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M9 11C9 11.5304 9.31607 12.0391 9.87868 12.4142C10.4413 12.7893 11.2044 13 12 13C12.7956 13 13.5587 12.7893 14.1213 12.4142C14.6839 12.0391 15 11.5304 15 11C15 10.4696 14.6839 9.96086 14.1213 9.58579C13.5587 9.21071 12.7956 9 12 9C11.2044 9 10.4413 9.21071 9.87868 9.58579C9.31607 9.96086 9 10.4696 9 11Z"/>
      <path d="M2 12.5C2 14.7543 3.05357 16.9163 4.92893 18.5104C6.8043 20.1045 9.34784 21 12 21C14.6522 21 17.1957 20.1045 19.0711 18.5104C20.9464 16.9163 22 14.7543 22 12.5C22 10.2457 20.9464 8.08365 19.0711 6.48959C17.1957 4.89553 14.6522 4 12 4C9.34784 4 6.8043 4.89553 4.92893 6.48959C3.05357 8.08365 2 10.2457 2 12.5Z"/>

    </svg>
  );
}
