import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function VolleyballIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M11.1 7.09998C15.0971 7.07325 18.9689 8.49408 22 11.1"/>
      <path d="M12 12C10.9697 13.3849 9.66583 14.5433 8.16926 15.4034C6.67268 16.2635 5.01534 16.807 3.30005 17"/>
      <path d="M16.8 13.5996C14.8148 17.1133 11.6141 19.7806 7.80005 21.0996"/>
      <path d="M20.7 17C19.6614 15.6235 18.3554 14.4711 16.8604 13.6119C15.3654 12.7527 13.7122 12.2044 12 12C10.6992 8.79358 10.6992 5.20642 12 2"/>
      <path d="M6.29997 3.7998C5.51781 7.73671 6.19305 11.8237 8.19997 15.2998"/>
      <path d="M2 12C2 14.6522 3.05357 17.1957 4.92893 19.0711C6.8043 20.9464 9.34784 22 12 22C14.6522 22 17.1957 20.9464 19.0711 19.0711C20.9464 17.1957 22 14.6522 22 12C22 9.34784 20.9464 6.8043 19.0711 4.92893C17.1957 3.05357 14.6522 2 12 2C9.34784 2 6.8043 3.05357 4.92893 4.92893C3.05357 6.8043 2 9.34784 2 12Z"/>

    </svg>
  );
}
