import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function BananaIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M4 13.0002C7.5 11.0002 12 11.0002 14 15.0002C14.8461 14.5682 15.7897 14.3628 16.7389 14.4039C17.688 14.445 18.6103 14.7312 19.4159 15.2347C20.2216 15.7383 20.883 16.4419 21.3359 17.277C21.7887 18.1122 22.0175 19.0504 22 20.0002"/>
      <path d="M5.15 17.89C10.67 16.37 13.8 11 12.15 5.89C11.55 4 11.5 2 13 2C16.22 2 18 7.5 18 10C18 16.5 13.8 22 7.51 22C5.11 22 2 22 2 20C2 18.5 3.14 18.45 5.15 17.89Z"/>

    </svg>
  );
}
