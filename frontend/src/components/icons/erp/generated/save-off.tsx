import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function SaveOffIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <g clip-path="url(#clip0_360_230)">
      <path d="M13 13H8C7.73478 13 7.48043 13.1054 7.29289 13.2929C7.10536 13.4804 7 13.7348 7 14V21"/>
      <path d="M14 8H15"/>
      <path d="M17 21V17"/>
      <path d="M2 2L22 22"/>
      <path d="M20.41 20.4098C20.0366 20.7854 19.5296 20.9976 19 20.9998H5C4.46957 20.9998 3.96086 20.7891 3.58579 20.4141C3.21071 20.039 3 19.5303 3 18.9998V4.99984C3.00223 4.47027 3.21441 3.96319 3.59 3.58984"/>
      <path d="M9 3H15.2C15.7275 3.00751 16.2307 3.22317 16.6 3.6L20.4 7.4C20.7768 7.76926 20.9925 8.27246 21 8.8V15"/>
      </g>
      <defs>
      <clipPath id="clip0_360_230">
      <rect width="24" height="24"/>
      </clipPath>
      </defs>

    </svg>
  );
}
