import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function BlindsIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M3 3H21"/>
      <path d="M20 7H8"/>
      <path d="M20 11H8"/>
      <path d="M10 19H20"/>
      <path d="M8 15H20"/>
      <path d="M4 3V17"/>
      <path d="M2 19C2 19.5304 2.21071 20.0391 2.58579 20.4142C2.96086 20.7893 3.46957 21 4 21C4.53043 21 5.03914 20.7893 5.41421 20.4142C5.78929 20.0391 6 19.5304 6 19C6 18.4696 5.78929 17.9609 5.41421 17.5858C5.03914 17.2107 4.53043 17 4 17C3.46957 17 2.96086 17.2107 2.58579 17.5858C2.21071 17.9609 2 18.4696 2 19Z"/>

    </svg>
  );
}
