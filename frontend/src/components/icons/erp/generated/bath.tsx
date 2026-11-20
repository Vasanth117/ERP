import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function BathIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M10 4L8 6"/>
      <path d="M17 19V21"/>
      <path d="M2 12H22"/>
      <path d="M7 19V21"/>
      <path d="M9 4.9998L7.621 3.6208C7.33181 3.33027 6.96463 3.12977 6.56388 3.04354C6.16313 2.95732 5.74598 2.98908 5.36289 3.13497C4.97981 3.28086 4.64721 3.53463 4.40533 3.86559C4.16346 4.19655 4.02267 4.59051 4 4.9998V16.9998C4 17.5302 4.21071 18.0389 4.58579 18.414C4.96086 18.7891 5.46957 18.9998 6 18.9998H18C18.5304 18.9998 19.0391 18.7891 19.4142 18.414C19.7893 18.0389 20 17.5302 20 16.9998V11.9998"/>

    </svg>
  );
}
