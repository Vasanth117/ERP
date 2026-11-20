import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ChartBarStackedIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M11 13V17"/>
      <path d="M15 5V9"/>
      <path d="M3 3V19C3 19.5304 3.21071 20.0391 3.58579 20.4142C3.96086 20.7893 4.46957 21 5 21H21"/>
      <path d="M8 13H15C15.2652 13 15.5196 13.1054 15.7071 13.2929C15.8946 13.4804 16 13.7348 16 14V16C16 16.2652 15.8946 16.5196 15.7071 16.7071C15.5196 16.8946 15.2652 17 15 17H8C7.73478 17 7.48043 16.8946 7.29289 16.7071C7.10536 16.5196 7 16.2652 7 16V14C7 13.7348 7.10536 13.4804 7.29289 13.2929C7.48043 13.1054 7.73478 13 8 13Z"/>
      <path d="M8 5H18C18.2652 5 18.5196 5.10536 18.7071 5.29289C18.8946 5.48043 19 5.73478 19 6V8C19 8.26522 18.8946 8.51957 18.7071 8.70711C18.5196 8.89464 18.2652 9 18 9H8C7.73478 9 7.48043 8.89464 7.29289 8.70711C7.10536 8.51957 7 8.26522 7 8V6C7 5.73478 7.10536 5.48043 7.29289 5.29289C7.48043 5.10536 7.73478 5 8 5Z"/>

    </svg>
  );
}
