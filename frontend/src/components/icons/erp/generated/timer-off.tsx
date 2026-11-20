import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function TimerOffIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M10 2H14"/>
      <path d="M4.59999 11C3.99419 12.4562 3.83235 14.059 4.13482 15.607C4.43729 17.1549 5.19058 18.5789 6.29999 19.7C7.42107 20.8094 8.84506 21.5627 10.393 21.8652C11.9409 22.1676 13.5438 22.0058 15 21.4"/>
      <path d="M7.40002 7.39979C8.95712 6.31945 10.8472 5.82697 12.7335 6.01011C14.6198 6.19325 16.3798 7.0401 17.7 8.39979C19.019 9.72647 19.8313 11.4734 19.9957 13.3369C20.1601 15.2004 19.6663 17.0627 18.6 18.5998"/>
      <path d="M2 2L22 22"/>
      <path d="M12 12V10"/>

    </svg>
  );
}
