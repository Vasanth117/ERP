import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function HdmiPortIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M22 9C22 8.73478 21.8946 8.48043 21.7071 8.29289C21.5196 8.10536 21.2652 8 21 8H3C2.73478 8 2.48043 8.10536 2.29289 8.29289C2.10536 8.48043 2 8.73478 2 9V13C2 13.2652 2.10536 13.5196 2.29289 13.7071C2.48043 13.8946 2.73478 14 3 14H4L6 16H18L20 14H21C21.2652 14 21.5196 13.8946 21.7071 13.7071C21.8946 13.5196 22 13.2652 22 13V9Z"/>
      <path d="M7.5 12H16.5"/>

    </svg>
  );
}
