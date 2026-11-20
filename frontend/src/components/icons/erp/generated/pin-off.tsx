import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function PinOffIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M12 17V22"/>
      <path d="M15 9.34V7C15 6.73478 15.1054 6.48043 15.2929 6.29289C15.4804 6.10536 15.7348 6 16 6C16.5304 6 17.0392 5.78929 17.4142 5.41421C17.7893 5.03914 18 4.53043 18 4C18 3.46957 17.7893 2.96086 17.4142 2.58579C17.0392 2.21071 16.5304 2 16 2H7.89001"/>
      <path d="M2 2L22 22"/>
      <path d="M9 9V10.76C8.9998 11.1321 8.89581 11.4967 8.69972 11.813C8.50363 12.1292 8.22321 12.3844 7.89 12.55L6.11 13.45C5.77679 13.6156 5.49637 13.8708 5.30028 14.187C5.10419 14.5033 5.0002 14.8679 5 15.24V16C5 16.2652 5.10536 16.5196 5.29289 16.7071C5.48043 16.8946 5.73478 17 6 17H17"/>

    </svg>
  );
}
