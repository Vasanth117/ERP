import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function UserRoundXIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M2 21C2 19.6081 2.36317 18.2402 3.05363 17.0316C3.74409 15.823 4.73794 14.8155 5.93699 14.1086C7.13604 13.4016 8.49879 13.0198 9.89059 13.0007C11.2824 12.9817 12.6551 13.3261 13.873 14"/>
      <path d="M5 8C5 9.32608 5.52678 10.5979 6.46447 11.5355C7.40215 12.4732 8.67392 13 10 13C11.3261 13 12.5979 12.4732 13.5355 11.5355C14.4732 10.5979 15 9.32608 15 8C15 6.67392 14.4732 5.40215 13.5355 4.46447C12.5979 3.52678 11.3261 3 10 3C8.67392 3 7.40215 3.52678 6.46447 4.46447C5.52678 5.40215 5 6.67392 5 8Z"/>
      <path d="M17 17L22 22"/>
      <path d="M22 17L17 22"/>

    </svg>
  );
}
