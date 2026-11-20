import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function CastIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M2 8V6C2 5.46957 2.21071 4.96086 2.58579 4.58579C2.96086 4.21071 3.46957 4 4 4H20C20.5304 4 21.0391 4.21071 21.4142 4.58579C21.7893 4.96086 22 5.46957 22 6V18C22 18.5304 21.7893 19.0391 21.4142 19.4142C21.0391 19.7893 20.5304 20 20 20H14"/>
      <path d="M2 12C4.04738 12.2173 5.95837 13.1299 7.41421 14.5858C8.87006 16.0416 9.78273 17.9526 10 20"/>
      <path d="M2 16C2.99265 16.1849 3.90608 16.666 4.62006 17.3799C5.33404 18.0939 5.81512 19.0073 6 20"/>
      <path d="M2 20H2.01"/>

    </svg>
  );
}
