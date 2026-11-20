import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function UngroupIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M6 4H12C12.2652 4 12.5196 4.10536 12.7071 4.29289C12.8946 4.48043 13 4.73478 13 5V9C13 9.26522 12.8946 9.51957 12.7071 9.70711C12.5196 9.89464 12.2652 10 12 10H6C5.73478 10 5.48043 9.89464 5.29289 9.70711C5.10536 9.51957 5 9.26522 5 9V5C5 4.73478 5.10536 4.48043 5.29289 4.29289C5.48043 4.10536 5.73478 4 6 4Z"/>
      <path d="M12 14H18C18.2652 14 18.5196 14.1054 18.7071 14.2929C18.8946 14.4804 19 14.7348 19 15V19C19 19.2652 18.8946 19.5196 18.7071 19.7071C18.5196 19.8946 18.2652 20 18 20H12C11.7348 20 11.4804 19.8946 11.2929 19.7071C11.1054 19.5196 11 19.2652 11 19V15C11 14.7348 11.1054 14.4804 11.2929 14.2929C11.4804 14.1054 11.7348 14 12 14Z"/>

    </svg>
  );
}
