import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function TriangleAlertIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M21.73 18.0002L13.73 4.00022C13.5556 3.69243 13.3026 3.43641 12.9969 3.25829C12.6912 3.08017 12.3438 2.98633 11.99 2.98633C11.6362 2.98633 11.2887 3.08017 10.9831 3.25829C10.6774 3.43641 10.4244 3.69243 10.25 4.00022L2.24999 18.0002C2.07367 18.3056 1.98122 18.6521 1.982 19.0047C1.98278 19.3573 2.07677 19.7035 2.25444 20.008C2.43211 20.3126 2.68714 20.5648 2.99369 20.7391C3.30023 20.9133 3.6474 21.0034 3.99999 21.0002H20C20.3509 20.9999 20.6955 20.9072 20.9993 20.7315C21.303 20.5558 21.5552 20.3033 21.7305 19.9993C21.9058 19.6954 21.998 19.3506 21.9979 18.9997C21.9978 18.6488 21.9054 18.3041 21.73 18.0002Z"/>
      <path d="M12 9V13"/>
      <path d="M12 17H12.01"/>

    </svg>
  );
}
