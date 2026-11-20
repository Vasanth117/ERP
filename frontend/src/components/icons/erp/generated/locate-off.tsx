import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function LocateOffIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M2 12H5"/>
      <path d="M19 12H22"/>
      <path d="M12 2V5"/>
      <path d="M12 19V22"/>
      <path d="M7.11 7.11035C5.83 8.39035 5 10.1004 5 12.0004C5 15.8704 8.13 19.0004 12 19.0004C13.9 19.0004 15.61 18.1704 16.89 16.8904"/>
      <path d="M18.71 13.96C18.9 13.33 19 12.67 19 12C19 8.13 15.87 5 12 5C11.33 5 10.67 5.1 10.04 5.29"/>
      <path d="M2 2L22 22"/>

    </svg>
  );
}
