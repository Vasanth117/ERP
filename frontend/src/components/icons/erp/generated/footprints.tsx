import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function FootprintsIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M4.00003 16V13.62C4.00003 11.5 2.97003 10.5 3.00003 8C3.03003 5.28 4.49003 2 7.50003 2C9.37003 2 10 3.8 10 5.5C10 8.61 8.00003 11.16 8.00003 14.18V16C8.00003 16.5304 7.78932 17.0391 7.41425 17.4142C7.03917 17.7893 6.53047 18 6.00003 18C5.4696 18 4.96089 17.7893 4.58582 17.4142C4.21075 17.0391 4.00003 16.5304 4.00003 16Z"/>
      <path d="M20 20V17.62C20 15.5 21.03 14.5 21 12C20.97 9.28 19.51 6 16.5 6C14.63 6 14 7.8 14 9.5C14 12.61 16 15.16 16 18.18V20C16 20.5304 16.2107 21.0391 16.5858 21.4142C16.9609 21.7893 17.4696 22 18 22C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20Z"/>
      <path d="M16 17H20"/>
      <path d="M4 13H8"/>

    </svg>
  );
}
