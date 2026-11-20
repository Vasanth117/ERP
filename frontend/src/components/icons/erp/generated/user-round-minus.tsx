import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function UserRoundMinusIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M2 21C1.99992 19.4603 2.44413 17.9534 3.27935 16.6599C4.11456 15.3664 5.30527 14.3415 6.7086 13.708C8.11193 13.0746 9.66824 12.8595 11.1908 13.0887C12.7133 13.3179 14.1373 13.9815 15.292 15"/>
      <path d="M5 8C5 9.32608 5.52678 10.5979 6.46447 11.5355C7.40215 12.4732 8.67392 13 10 13C11.3261 13 12.5979 12.4732 13.5355 11.5355C14.4732 10.5979 15 9.32608 15 8C15 6.67392 14.4732 5.40215 13.5355 4.46447C12.5979 3.52678 11.3261 3 10 3C8.67392 3 7.40215 3.52678 6.46447 4.46447C5.52678 5.40215 5 6.67392 5 8Z"/>
      <path d="M22 19H16"/>

    </svg>
  );
}
