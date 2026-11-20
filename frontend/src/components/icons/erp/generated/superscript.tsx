import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function SuperscriptIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M4 19L12 11"/>
      <path d="M12 19L4 11"/>
      <path d="M20 11.9998H16C16 10.4998 16.442 9.99978 17.5 9.49978C18.558 8.99978 20 8.33378 20 7.00178C20 6.52978 19.83 6.07178 19.516 5.71178C19.196 5.34985 18.7613 5.10899 18.2848 5.0296C17.8083 4.95021 17.319 5.03713 16.899 5.27578C16.479 5.51478 16.161 5.88978 16 6.33578"/>

    </svg>
  );
}
