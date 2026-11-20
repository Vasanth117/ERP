import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function Link2Icon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M9 17H7C5.67392 17 4.40215 16.4732 3.46447 15.5355C2.52678 14.5979 2 13.3261 2 12C2 10.6739 2.52678 9.40215 3.46447 8.46447C4.40215 7.52678 5.67392 7 7 7H9"/>
      <path d="M15 7H17C18.3261 7 19.5979 7.52678 20.5355 8.46447C21.4732 9.40215 22 10.6739 22 12C22 13.3261 21.4732 14.5979 20.5355 15.5355C19.5979 16.4732 18.3261 17 17 17H15"/>
      <path d="M8 12H16"/>

    </svg>
  );
}
