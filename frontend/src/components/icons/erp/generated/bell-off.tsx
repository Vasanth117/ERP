import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function BellOffIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M8.70001 3.00001C9.60382 2.4048 10.6518 2.06511 11.7329 2.01694C12.814 1.96876 13.8881 2.21388 14.8412 2.72634C15.7944 3.23879 16.5912 3.99951 17.1473 4.9279C17.7034 5.8563 17.998 6.91781 18 8.00001C18.0016 9.68453 18.203 11.3629 18.6 13"/>
      <path d="M17 17H3C3 17 6 15 6 8.00005C5.99349 7.41966 6.09522 6.84315 6.3 6.30005"/>
      <path d="M10.3 21C10.4674 21.3044 10.7134 21.5583 11.0125 21.7352C11.3115 21.912 11.6526 22.0053 12 22.0053C12.3474 22.0053 12.6885 21.912 12.9875 21.7352C13.2865 21.5583 13.5326 21.3044 13.7 21"/>
      <path d="M2 2L22 22"/>

    </svg>
  );
}
