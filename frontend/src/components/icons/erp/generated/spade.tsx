import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function SpadeIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M5 9C3.5 10.5 2 12.2 2 14.5C2 15.2223 2.14226 15.9375 2.41866 16.6048C2.69506 17.272 3.10019 17.8784 3.61091 18.3891C4.64236 19.4205 6.04131 20 7.5 20C9.3 20 10.5 19.5 12 18C13.5 19.5 14.7 20 16.5 20C17.2223 20 17.9375 19.8577 18.6048 19.5813C19.272 19.3049 19.8784 18.8998 20.3891 18.3891C20.8998 17.8784 21.3049 17.272 21.5813 16.6048C21.8577 15.9375 22 15.2223 22 14.5C22 12.2 20.5 10.5 19 9L12 2L5 9Z"/>
      <path d="M12 18V22"/>

    </svg>
  );
}
