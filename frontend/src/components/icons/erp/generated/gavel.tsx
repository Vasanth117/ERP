import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function GavelIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M14.5 12.5L6.49998 20.5C6.10216 20.8978 5.56259 21.1213 4.99998 21.1213C4.43737 21.1213 3.89781 20.8978 3.49998 20.5C3.10216 20.1022 2.87866 19.5626 2.87866 19C2.87866 18.4374 3.10216 17.8978 3.49998 17.5L11.5 9.5"/>
      <path d="M16 16L22 10"/>
      <path d="M8 8L14 2"/>
      <path d="M9 7L17 15"/>
      <path d="M21 11L13 3"/>

    </svg>
  );
}
