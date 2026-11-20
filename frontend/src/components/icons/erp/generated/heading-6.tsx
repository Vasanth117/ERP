import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function Heading6Icon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M4 12H12"/>
      <path d="M4 18V6"/>
      <path d="M12 18V6"/>
      <path d="M17 16C17 16.5304 17.2107 17.0391 17.5858 17.4142C17.9609 17.7893 18.4696 18 19 18C19.5304 18 20.0391 17.7893 20.4142 17.4142C20.7893 17.0391 21 16.5304 21 16C21 15.4696 20.7893 14.9609 20.4142 14.5858C20.0391 14.2107 19.5304 14 19 14C18.4696 14 17.9609 14.2107 17.5858 14.5858C17.2107 14.9609 17 15.4696 17 16Z"/>
      <path d="M20 10C18 12 17 13.5 17 16"/>

    </svg>
  );
}
