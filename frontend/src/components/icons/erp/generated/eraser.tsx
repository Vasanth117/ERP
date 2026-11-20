import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function EraserIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M7 21.0002L2.7 16.7002C1.7 15.7002 1.7 14.2002 2.7 13.3002L12.3 3.7002C13.3 2.7002 14.8 2.7002 15.7 3.7002L21.3 9.3002C22.3 10.3002 22.3 11.8002 21.3 12.7002L13 21.0002"/>
      <path d="M22 21H7"/>
      <path d="M5 11L14 20"/>

    </svg>
  );
}
