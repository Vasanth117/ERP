import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function SpaceIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M22 17V18C22 18.5 21.5 19 21 19H3C2.5 19 2 18.5 2 18V17"/>

    </svg>
  );
}
