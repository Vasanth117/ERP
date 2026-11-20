import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function LightbulbOffIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M16.8 11.1998C17.6 10.2998 18 9.19976 18 7.99976C17.998 6.91757 17.7034 5.85606 17.1473 4.92766C16.5912 3.99926 15.7944 3.23855 14.8412 2.72609C13.8881 2.21364 12.814 1.96851 11.7329 2.01669C10.6518 2.06487 9.60382 2.40455 8.70001 2.99976"/>
      <path d="M2 2L22 22"/>
      <path d="M6.30002 6.2998C5.9449 7.18536 5.86953 8.15843 6.08407 9.0881C6.29861 10.0178 6.79276 10.8594 7.50002 11.4998C8.20002 12.1998 8.80002 12.9998 9.00002 13.9998"/>
      <path d="M9 18H15"/>
      <path d="M10 22H14"/>

    </svg>
  );
}
