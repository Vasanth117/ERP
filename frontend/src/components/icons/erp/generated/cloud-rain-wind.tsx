import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function CloudRainWindIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M3.99997 14.8993C3.25701 14.1402 2.69654 13.222 2.36101 12.2142C2.02547 11.2064 1.92368 10.1355 2.06333 9.08256C2.20299 8.02962 2.58043 7.02226 3.16707 6.1368C3.75371 5.25133 4.53416 4.51098 5.44931 3.97182C6.36445 3.43265 7.3903 3.10882 8.44914 3.02484C9.50798 2.94087 10.572 3.09895 11.5607 3.48712C12.5494 3.8753 13.4368 4.48337 14.1557 5.2653C14.8746 6.04723 15.4061 6.9825 15.71 8.00026H17.5C18.4655 8.00015 19.4054 8.31059 20.181 8.8857C20.9565 9.46082 21.5265 10.2701 21.8067 11.1941C22.087 12.118 22.0627 13.1076 21.7373 14.0166C21.412 14.9257 20.8028 15.706 20 16.2423"/>
      <path d="M9.20001 22L12.2 15"/>
      <path d="M9 13L6 20"/>
      <path d="M17 13L14 20"/>

    </svg>
  );
}
