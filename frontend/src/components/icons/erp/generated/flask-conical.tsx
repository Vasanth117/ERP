import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function FlaskConicalIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M9.99999 2V9.527C10.0003 9.83801 9.92803 10.1448 9.78899 10.423L4.71999 20.55C4.64289 20.703 4.60639 20.8732 4.61399 21.0444C4.62159 21.2155 4.67302 21.3818 4.76337 21.5274C4.85371 21.6729 4.97994 21.7928 5.12994 21.8756C5.27994 21.9584 5.44868 22.0012 5.61999 22H18.38C18.5513 22.0012 18.72 21.9584 18.87 21.8756C19.02 21.7928 19.1463 21.6729 19.2366 21.5274C19.327 21.3818 19.3784 21.2155 19.386 21.0444C19.3936 20.8732 19.3571 20.703 19.28 20.55L14.211 10.423C14.0719 10.1448 13.9997 9.83801 14 9.527V2"/>
      <path d="M8.5 2H15.5"/>
      <path d="M7 16H17"/>

    </svg>
  );
}
