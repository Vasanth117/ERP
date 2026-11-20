import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ArrowDown10Icon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M3 16L7 20L11 16"/>
      <path d="M7 20V4"/>
      <path d="M17 10V4H15"/>
      <path d="M15 10H19"/>
      <path d="M17 14C17.5304 14 18.0391 14.2107 18.4142 14.5858C18.7893 14.9609 19 15.4696 19 16V18C19 18.5304 18.7893 19.0391 18.4142 19.4142C18.0391 19.7893 17.5304 20 17 20C16.4696 20 15.9609 19.7893 15.5858 19.4142C15.2107 19.0391 15 18.5304 15 18V16C15 15.4696 15.2107 14.9609 15.5858 14.5858C15.9609 14.2107 16.4696 14 17 14Z"/>

    </svg>
  );
}
