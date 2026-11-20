import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function Heading2Icon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M21 17.9998H17C17 13.9998 21 14.9998 21 11.9998C21 10.4998 19 9.49982 17 10.9998"/>

    </svg>
  );
}
