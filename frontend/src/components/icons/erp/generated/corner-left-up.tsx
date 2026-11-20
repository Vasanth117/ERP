import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function CornerLeftUpIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M14 9L9 4L4 9"/>
      <path d="M20 20H13C11.9391 20 10.9217 19.5786 10.1716 18.8284C9.42143 18.0783 9 17.0609 9 16V4"/>

    </svg>
  );
}
