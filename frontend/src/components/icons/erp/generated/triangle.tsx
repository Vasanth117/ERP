import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function TriangleIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M13.73 4.00036C13.5542 3.69728 13.3019 3.44571 12.9983 3.27083C12.6946 3.09595 12.3504 3.00391 12 3.00391C11.6496 3.00391 11.3054 3.09595 11.0018 3.27083C10.6982 3.44571 10.4458 3.69728 10.27 4.00036L2.27003 18.0004C2.09458 18.3043 2.00217 18.6489 2.00208 18.9998C2.00199 19.3507 2.09422 19.6955 2.26951 19.9995C2.44481 20.3035 2.69699 20.556 3.00074 20.7316C3.3045 20.9073 3.64913 21 4.00003 21.0004H20C20.3509 21 20.6956 20.9073 20.9993 20.7316C21.3031 20.556 21.5552 20.3035 21.7305 19.9995C21.9058 19.6955 21.9981 19.3507 21.998 18.9998C21.9979 18.6489 21.9055 18.3043 21.73 18.0004L13.73 4.00036Z"/>

    </svg>
  );
}
