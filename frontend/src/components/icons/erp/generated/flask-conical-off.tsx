import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function FlaskConicalOffIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M10 10L4.72002 20.55C4.64293 20.703 4.60643 20.8732 4.61402 21.0444C4.62162 21.2155 4.67305 21.3818 4.7634 21.5274C4.85374 21.6729 4.97997 21.7928 5.12997 21.8756C5.27997 21.9584 5.44871 22.0012 5.62002 22H18.38C18.5513 22.0012 18.7201 21.9584 18.8701 21.8756C19.0201 21.7928 19.1463 21.6729 19.2366 21.5274C19.327 21.3818 19.3784 21.2155 19.386 21.0444C19.3936 20.8732 19.3571 20.703 19.28 20.55L18.008 18.008"/>
      <path d="M10 2V4.343"/>
      <path d="M14 2V8.343"/>
      <path d="M8.5 2H15.5"/>
      <path d="M7 16H16"/>
      <path d="M2 2L22 22"/>

    </svg>
  );
}
