import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ShowerHeadIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M4 4L6.5 6.5"/>
      <path d="M13.5 6.49961C12.5685 5.58679 11.3145 5.07844 10.0103 5.08502C8.70618 5.09161 7.45733 5.6126 6.53515 6.53478C5.61297 7.45696 5.09198 8.70582 5.08539 10.01C5.0788 11.3141 5.58715 12.5682 6.49997 13.4996"/>
      <path d="M15 5L5 15"/>
      <path d="M14 17V17.01"/>
      <path d="M10 16V16.01"/>
      <path d="M13 13V13.01"/>
      <path d="M16 10V10.01"/>
      <path d="M11 20V20.01"/>
      <path d="M17 14V14.01"/>
      <path d="M20 11V11.01"/>

    </svg>
  );
}
