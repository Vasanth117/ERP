import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ArrowUpFromLineIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M18 9L12 3L6 9"/>
      <path d="M12 3V17"/>
      <path d="M5 21H19"/>

    </svg>
  );
}
