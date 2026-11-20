import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function MessageCircleOffIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M20.5 14.9001C21.0343 13.3119 21.1146 11.6061 20.7319 9.97469C20.3492 8.34332 19.5186 6.85119 18.3338 5.66631C17.1489 4.48144 15.6568 3.65088 14.0254 3.26816C12.394 2.88545 10.6882 2.96577 9.10001 3.50008"/>
      <path d="M2 2L22 22"/>
      <path d="M5.6 5.6001C3 8.3001 2.2 12.5001 4 16.0001L2 22.0001L8 20.0001C11.4 21.8001 15.6 21.1001 18.3 18.3001"/>

    </svg>
  );
}
