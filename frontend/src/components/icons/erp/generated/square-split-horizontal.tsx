import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function SquareSplitHorizontalIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M8 19H5C4 19 3 18 3 17V7C3 6 4 5 5 5H8"/>
      <path d="M16 5H19C20 5 21 6 21 7V17C21 18 20 19 19 19H16"/>
      <path d="M12 4V20"/>

    </svg>
  );
}
