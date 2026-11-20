import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function TestTubeIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M14.5 2V19.5C14.5 20.9 13.4 22 12 22C10.6 22 9.5 20.9 9.5 19.5V2"/>
      <path d="M8.5 2H15.5"/>
      <path d="M14.5 16H9.5"/>

    </svg>
  );
}
