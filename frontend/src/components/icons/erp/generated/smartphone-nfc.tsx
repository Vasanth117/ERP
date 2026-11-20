import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function SmartphoneNfcIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M3 6H8C8.26522 6 8.51957 6.10536 8.70711 6.29289C8.89464 6.48043 9 6.73478 9 7V17C9 17.2652 8.89464 17.5196 8.70711 17.7071C8.51957 17.8946 8.26522 18 8 18H3C2.73478 18 2.48043 17.8946 2.29289 17.7071C2.10536 17.5196 2 17.2652 2 17V7C2 6.73478 2.10536 6.48043 2.29289 6.29289C2.48043 6.10536 2.73478 6 3 6Z"/>
      <path d="M13 8.31982C13.6392 9.44097 13.9754 10.7093 13.9754 11.9998C13.9754 13.2904 13.6392 14.5587 13 15.6798"/>
      <path d="M16.46 6.20996C17.4591 7.97615 17.9841 9.97079 17.9841 12C17.9841 14.0291 17.4591 16.0238 16.46 17.79"/>
      <path d="M19.91 4.1001C21.2876 6.50473 22.0131 9.22749 22.0149 11.9988C22.0167 14.77 21.2945 17.4937 19.92 19.9001"/>

    </svg>
  );
}
