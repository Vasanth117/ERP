import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function CakeIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M20 21V13C20 12.4696 19.7893 11.9609 19.4142 11.5858C19.0391 11.2107 18.5304 11 18 11H6C5.46957 11 4.96086 11.2107 4.58579 11.5858C4.21071 11.9609 4 12.4696 4 13V21"/>
      <path d="M4 16C4 16 4.5 15 6 15C7.5 15 8.5 17 10 17C11.5 17 12.5 15 14 15C15.5 15 16.5 17 18 17C19.5 17 20 16 20 16"/>
      <path d="M2 21H22"/>
      <path d="M7 8V11"/>
      <path d="M12 8V11"/>
      <path d="M17 8V11"/>
      <path d="M7 4H7.01"/>
      <path d="M12 4H12.01"/>
      <path d="M17 4H17.01"/>

    </svg>
  );
}
