import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function PilcrowIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M13 4V20"/>
      <path d="M17 4V20"/>
      <path d="M19 4H9.5C8.30653 4 7.16193 4.47411 6.31802 5.31802C5.47411 6.16193 5 7.30653 5 8.5C5 9.69347 5.47411 10.8381 6.31802 11.682C7.16193 12.5259 8.30653 13 9.5 13H13"/>

    </svg>
  );
}
