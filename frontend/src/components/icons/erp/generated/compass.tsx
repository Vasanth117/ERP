import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function CompassIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M16.24 7.75977L14.436 13.1708C14.3378 13.4653 14.1724 13.733 13.9528 13.9526C13.7333 14.1722 13.4656 14.3376 13.171 14.4358L7.76001 16.2398L9.56401 10.8288C9.66219 10.5342 9.82762 10.2665 10.0472 10.0469C10.2668 9.82737 10.5344 9.66195 10.829 9.56377L16.24 7.75977Z"/>
      <path d="M2 12C2 14.6522 3.05357 17.1957 4.92893 19.0711C6.8043 20.9464 9.34784 22 12 22C14.6522 22 17.1957 20.9464 19.0711 19.0711C20.9464 17.1957 22 14.6522 22 12C22 9.34784 20.9464 6.8043 19.0711 4.92893C17.1957 3.05357 14.6522 2 12 2C9.34784 2 6.8043 3.05357 4.92893 4.92893C3.05357 6.8043 2 9.34784 2 12Z"/>

    </svg>
  );
}
