import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function Music2Icon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M4 18C4 19.0609 4.42143 20.0783 5.17157 20.8284C5.92172 21.5786 6.93913 22 8 22C9.06087 22 10.0783 21.5786 10.8284 20.8284C11.5786 20.0783 12 19.0609 12 18C12 16.9391 11.5786 15.9217 10.8284 15.1716C10.0783 14.4214 9.06087 14 8 14C6.93913 14 5.92172 14.4214 5.17157 15.1716C4.42143 15.9217 4 16.9391 4 18Z"/>
      <path d="M12 18V2L19 6"/>

    </svg>
  );
}
