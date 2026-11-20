import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function HardHatIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M10 10V5C10 4.73478 10.1054 4.48043 10.2929 4.29289C10.4804 4.10536 10.7348 4 11 4H13C13.2652 4 13.5196 4.10536 13.7071 4.29289C13.8946 4.48043 14 4.73478 14 5V10"/>
      <path d="M14 6C15.5913 6 17.1174 6.63214 18.2426 7.75736C19.3679 8.88258 20 10.4087 20 12V15"/>
      <path d="M4 15V12C4 10.4087 4.63214 8.88258 5.75736 7.75736C6.88258 6.63214 8.4087 6 10 6"/>
      <path d="M3 15H21C21.2652 15 21.5196 15.1054 21.7071 15.2929C21.8946 15.4804 22 15.7348 22 16V18C22 18.2652 21.8946 18.5196 21.7071 18.7071C21.5196 18.8946 21.2652 19 21 19H3C2.73478 19 2.48043 18.8946 2.29289 18.7071C2.10536 18.5196 2 18.2652 2 18V16C2 15.7348 2.10536 15.4804 2.29289 15.2929C2.48043 15.1054 2.73478 15 3 15Z"/>

    </svg>
  );
}
