import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ChartNoAxesCombinedIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M12 16V21"/>
      <path d="M16 14V21"/>
      <path d="M20 10V21"/>
      <path d="M22 3L13.354 11.646C13.3076 11.6926 13.2524 11.7295 13.1916 11.7547C13.1309 11.7799 13.0658 11.7929 13 11.7929C12.9342 11.7929 12.8691 11.7799 12.8084 11.7547C12.7476 11.7295 12.6924 11.6926 12.646 11.646L9.354 8.354C9.26024 8.26026 9.13308 8.20761 9.0005 8.20761C8.86792 8.20761 8.74076 8.26026 8.647 8.354L2 15"/>
      <path d="M4 18V21"/>
      <path d="M8 14V21"/>

    </svg>
  );
}
