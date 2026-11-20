import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function UsersRoundIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M18 21C18 18.8783 17.1571 16.8434 15.6569 15.3431C14.1566 13.8429 12.1217 13 10 13C7.87827 13 5.84344 13.8429 4.34315 15.3431C2.84285 16.8434 2 18.8783 2 21"/>
      <path d="M5 8C5 9.32608 5.52678 10.5979 6.46447 11.5355C7.40215 12.4732 8.67392 13 10 13C11.3261 13 12.5979 12.4732 13.5355 11.5355C14.4732 10.5979 15 9.32608 15 8C15 6.67392 14.4732 5.40215 13.5355 4.46447C12.5979 3.52678 11.3261 3 10 3C8.67392 3 7.40215 3.52678 6.46447 4.46447C5.52678 5.40215 5 6.67392 5 8Z"/>
      <path d="M22 20C22 16.63 20 13.5 18 12C18.6575 11.5068 19.1832 10.8591 19.5306 10.1143C19.8781 9.36946 20.0366 8.55048 19.9921 7.72981C19.9476 6.90914 19.7015 6.1121 19.2755 5.40921C18.8496 4.70633 18.2569 4.11927 17.55 3.70001"/>

    </svg>
  );
}
