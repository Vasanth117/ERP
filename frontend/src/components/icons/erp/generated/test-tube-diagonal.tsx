import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function TestTubeDiagonalIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M21 7L6.82 21.18C6.28846 21.7057 5.57052 21.9997 4.82294 21.9978C4.07537 21.9959 3.35891 21.6983 2.83 21.17C2.29996 20.6394 2.00223 19.92 2.00223 19.17C2.00223 18.42 2.29996 17.7006 2.83 17.17L17 3"/>
      <path d="M16 2L22 8"/>
      <path d="M12 16H4"/>

    </svg>
  );
}
