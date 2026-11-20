import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ToyBrickIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M4 8H20C20.2652 8 20.5196 8.10536 20.7071 8.29289C20.8946 8.48043 21 8.73478 21 9V19C21 19.2652 20.8946 19.5196 20.7071 19.7071C20.5196 19.8946 20.2652 20 20 20H4C3.73478 20 3.48043 19.8946 3.29289 19.7071C3.10536 19.5196 3 19.2652 3 19V9C3 8.73478 3.10536 8.48043 3.29289 8.29289C3.48043 8.10536 3.73478 8 4 8Z"/>
      <path d="M10 8V5C10 4.4 9.6 4 9 4H6C5.73478 4 5.48043 4.10536 5.29289 4.29289C5.10536 4.48043 5 4.73478 5 5V8"/>
      <path d="M19 8V5C19 4.4 18.6 4 18 4H15C14.7348 4 14.4804 4.10536 14.2929 4.29289C14.1054 4.48043 14 4.73478 14 5V8"/>

    </svg>
  );
}
