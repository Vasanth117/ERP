import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function CircleHelpIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M9.09003 8.99959C9.32513 8.33126 9.78918 7.7677 10.4 7.40873C11.0108 7.04975 11.7289 6.91853 12.4272 7.0383C13.1255 7.15808 13.7588 7.52112 14.2151 8.06312C14.6714 8.60512 14.9211 9.29112 14.92 9.99959C14.92 11.9996 11.92 12.9996 11.92 12.9996"/>
      <path d="M12 17H12.01"/>

    </svg>
  );
}
