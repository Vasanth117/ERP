import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function FilterXIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M13.013 3H2L10 12.46V19L14 21V12.46L14.9 11.405"/>
      <path d="M22 3L17 8"/>
      <path d="M17 3L22 8"/>

    </svg>
  );
}
