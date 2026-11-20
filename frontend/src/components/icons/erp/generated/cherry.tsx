import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function CherryIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M2 17.0004C2 18.3265 2.52678 19.5982 3.46447 20.5359C4.40215 21.4736 5.67392 22.0004 7 22.0004C8.32608 22.0004 9.59785 21.4736 10.5355 20.5359C11.4732 19.5982 12 18.3265 12 17.0004C12 14.2404 9.5 12.0004 7 14.0004C4.5 12.0004 2 14.2404 2 17.0004Z"/>
      <path d="M12 17.0004C12 18.3265 12.5268 19.5982 13.4645 20.5359C14.4021 21.4736 15.6739 22.0004 17 22.0004C18.3261 22.0004 19.5979 21.4736 20.5355 20.5359C21.4732 19.5982 22 18.3265 22 17.0004C22 14.2404 19.5 12.0004 17 14.0004C14.5 12.0004 12 14.2404 12 17.0004Z"/>
      <path d="M7 14C10.22 11.09 11.29 5.25 12 2C13.66 4.38 16.94 11 17 14"/>
      <path d="M22 9C17.71 9 14.86 6.67 12 2C17.71 2 22 6.67 22 9Z"/>

    </svg>
  );
}
