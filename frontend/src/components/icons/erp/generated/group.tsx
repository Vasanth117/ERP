import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function GroupIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M3 7V5C3 3.9 3.9 3 5 3H7"/>
      <path d="M17 3H19C20.1 3 21 3.9 21 5V7"/>
      <path d="M21 17V19C21 20.1 20.1 21 19 21H17"/>
      <path d="M7 21H5C3.9 21 3 20.1 3 19V17"/>
      <path d="M8 7H13C13.2652 7 13.5196 7.10536 13.7071 7.29289C13.8946 7.48043 14 7.73478 14 8V11C14 11.2652 13.8946 11.5196 13.7071 11.7071C13.5196 11.8946 13.2652 12 13 12H8C7.73478 12 7.48043 11.8946 7.29289 11.7071C7.10536 11.5196 7 11.2652 7 11V8C7 7.73478 7.10536 7.48043 7.29289 7.29289C7.48043 7.10536 7.73478 7 8 7Z"/>
      <path d="M11 12H16C16.2652 12 16.5196 12.1054 16.7071 12.2929C16.8946 12.4804 17 12.7348 17 13V16C17 16.2652 16.8946 16.5196 16.7071 16.7071C16.5196 16.8946 16.2652 17 16 17H11C10.7348 17 10.4804 16.8946 10.2929 16.7071C10.1054 16.5196 10 16.2652 10 16V13C10 12.7348 10.1054 12.4804 10.2929 12.2929C10.4804 12.1054 10.7348 12 11 12Z"/>

    </svg>
  );
}
