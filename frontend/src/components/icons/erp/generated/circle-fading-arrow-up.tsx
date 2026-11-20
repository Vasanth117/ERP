import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function CircleFadingArrowUpIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M12 2C13.9401 1.99965 15.8385 2.56368 17.4637 3.62336C19.0889 4.68303 20.3707 6.19259 21.153 7.96804C21.9352 9.74349 22.1841 11.7082 21.8693 13.6226C21.5545 15.537 20.6896 17.3185 19.38 18.75"/>
      <path d="M16 12L12 8L8 12"/>
      <path d="M12 16V8"/>
      <path d="M2.5 8.875C2.18135 9.84366 2.01273 10.8554 2 11.875"/>
      <path d="M2.83002 16C3.39152 17.2918 4.2196 18.4505 5.26002 19.4"/>
      <path d="M4.63599 5.23493C4.91503 4.93116 5.2126 4.64495 5.52699 4.37793"/>
      <path d="M8.64398 21.42C11.1377 22.3084 13.8819 22.1718 16.275 21.04"/>

    </svg>
  );
}
