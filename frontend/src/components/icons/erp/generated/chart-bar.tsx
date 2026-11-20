import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ChartBarIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M3 3V19C3 19.5304 3.21071 20.0391 3.58579 20.4142C3.96086 20.7893 4.46957 21 5 21H21"/>
      <path d="M7 16H15"/>
      <path d="M7 11H19"/>
      <path d="M7 6H10"/>

    </svg>
  );
}
