import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function TheaterIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M2 10C2 10 5 7 5 2"/>
      <path d="M22 10C22 10 19 7 19 2"/>
      <path d="M10 2C10 6.4 6.4 10 2 10"/>
      <path d="M14 2C14 6.4 17.6 10 22 10"/>
      <path d="M2 10C2 10 4 12 4 15"/>
      <path d="M22 10C22 10 20 12 20 15"/>
      <path d="M8 15H16"/>
      <path d="M2 22V21C2 20.4696 2.21071 19.9609 2.58579 19.5858C2.96086 19.2107 3.46957 19 4 19H8C8.53043 19 9.03914 19.2107 9.41421 19.5858C9.78929 19.9609 10 20.4696 10 21V22"/>
      <path d="M14 22V21C14 20.4696 14.2107 19.9609 14.5858 19.5858C14.9609 19.2107 15.4696 19 16 19H20C20.5304 19 21.0391 19.2107 21.4142 19.5858C21.7893 19.9609 22 20.4696 22 21V22"/>

    </svg>
  );
}
