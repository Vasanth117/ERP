import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function SatelliteIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M13 7L9 3L5 7L9 11"/>
      <path d="M17 11L21 15L17 19L13 15"/>
      <path d="M8 12L12 16L18 10L14 6L8 12Z"/>
      <path d="M16 8L19 5"/>
      <path d="M9 21C9 19.4087 8.36786 17.8826 7.24264 16.7574C6.11742 15.6321 4.5913 15 3 15"/>

    </svg>
  );
}
