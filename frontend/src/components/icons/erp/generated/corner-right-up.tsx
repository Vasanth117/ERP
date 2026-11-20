import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function CornerRightUpIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M10 9L15 4L20 9"/>
      <path d="M4 20H11C12.0609 20 13.0783 19.5786 13.8284 18.8284C14.5786 18.0783 15 17.0609 15 16V4"/>

    </svg>
  );
}
