import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function DrumIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M2 2L10 10"/>
      <path d="M22 2L14 10"/>
      <path d="M2 9C2 10.3261 3.05357 11.5979 4.92893 12.5355C6.8043 13.4732 9.34784 14 12 14C14.6522 14 17.1957 13.4732 19.0711 12.5355C20.9464 11.5979 22 10.3261 22 9C22 7.67392 20.9464 6.40215 19.0711 5.46447C17.1957 4.52678 14.6522 4 12 4C9.34784 4 6.8043 4.52678 4.92893 5.46447C3.05357 6.40215 2 7.67392 2 9Z"/>
      <path d="M7 13.4004V21.3004"/>
      <path d="M12 14V22"/>
      <path d="M17 13.4004V21.3004"/>
      <path d="M2 9V17C2 18.3261 3.05357 19.5979 4.92893 20.5355C6.8043 21.4732 9.34784 22 12 22C14.6522 22 17.1957 21.4732 19.0711 20.5355C20.9464 19.5979 22 18.3261 22 17V9"/>

    </svg>
  );
}
