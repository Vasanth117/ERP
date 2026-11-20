import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function SliceIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M11 16.5861V19.0001C11 19.2653 10.8946 19.5197 10.7071 19.7072C10.5196 19.8948 10.2652 20.0001 10 20.0001H2L8 14.0001M11 16.5861C11.2652 16.5861 11.5195 16.4806 11.707 16.2931L21.37 6.63011C21.7678 6.23228 21.9913 5.69272 21.9913 5.13011C21.9913 4.5675 21.7678 4.02793 21.37 3.63011C20.9722 3.23228 20.4326 3.00879 19.87 3.00879C19.3074 3.00879 18.7678 3.23228 18.37 3.63011L8 14.0001M11 16.5861C10.7348 16.5861 10.4805 16.4806 10.293 16.2931L8 14.0001"/>

    </svg>
  );
}
