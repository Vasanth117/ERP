import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function Redo2Icon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M15 14L20 9L15 4"/>
      <path d="M20 9H9.5C8.04131 9 6.64236 9.57946 5.61091 10.6109C4.57946 11.6424 4 13.0413 4 14.5C4 15.2223 4.14226 15.9375 4.41866 16.6048C4.69506 17.272 5.10019 17.8784 5.61091 18.3891C6.64236 19.4205 8.04131 20 9.5 20H13"/>

    </svg>
  );
}
