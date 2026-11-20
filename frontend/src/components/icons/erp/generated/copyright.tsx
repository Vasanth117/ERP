import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function CopyrightIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M14.83 14.83C14.2704 15.389 13.5577 15.7695 12.7819 15.9235C12.0061 16.0774 11.2021 15.998 10.4714 15.6951C9.74077 15.3922 9.11632 14.8795 8.67699 14.2218C8.23766 13.5641 8.00317 12.7909 8.00317 12C8.00317 11.2091 8.23766 10.4359 8.67699 9.77818C9.11632 9.12048 9.74077 8.60779 10.4714 8.30491C11.2021 8.00203 12.0061 7.92256 12.7819 8.07654C13.5577 8.23052 14.2704 8.61104 14.83 9.17"/>

    </svg>
  );
}
