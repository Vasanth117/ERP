import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ClockArrowUpIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M13.228 21.9248C11.1988 22.1759 9.14143 21.799 7.33306 20.8448C5.52468 19.8907 4.05226 18.4051 3.11421 16.5883C2.17615 14.7715 1.81756 12.7108 2.08674 10.684C2.35593 8.6571 3.23996 6.76145 4.6197 5.25249C5.99944 3.74352 7.80858 2.69377 9.80332 2.24468C11.7981 1.79559 13.8825 1.96876 15.7758 2.74085C17.6691 3.51293 19.2802 4.84683 20.392 6.56278C21.5039 8.27873 22.063 10.2943 21.994 12.3378"/>
      <path d="M12 6V12L13.562 12.781"/>
      <path d="M14 18L18 14L22 18"/>
      <path d="M18 22V14"/>

    </svg>
  );
}
