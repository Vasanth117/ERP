import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function RadioIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M4.89998 19.0999C0.999976 15.1999 0.999976 8.7999 4.89998 4.8999"/>
      <path d="M7.80001 16.2C5.50001 13.9 5.50001 10.1 7.80001 7.69995"/>
      <path d="M10 12C10 12.5304 10.2107 13.0391 10.5858 13.4142C10.9609 13.7893 11.4696 14 12 14C12.5304 14 13.0391 13.7893 13.4142 13.4142C13.7893 13.0391 14 12.5304 14 12C14 11.4696 13.7893 10.9609 13.4142 10.5858C13.0391 10.2107 12.5304 10 12 10C11.4696 10 10.9609 10.2107 10.5858 10.5858C10.2107 10.9609 10 11.4696 10 12Z"/>
      <path d="M16.2 7.80005C18.5 10.1 18.5 13.9 16.2 16.3"/>
      <path d="M19.1 4.8999C23 8.7999 23 15.0999 19.1 18.9999"/>

    </svg>
  );
}
