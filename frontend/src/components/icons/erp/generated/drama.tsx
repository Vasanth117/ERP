import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function DramaIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M10 11H10.01"/>
      <path d="M14 6H14.01"/>
      <path d="M18 6H18.01"/>
      <path d="M6.5 13.0996H6.51"/>
      <path d="M22 5C22 14 18 17 16 17C14 17 10 14 10 5C10 3 12 2 16 2C20 2 22 3 22 5Z"/>
      <path d="M17.4 9.90039C16.6 10.7004 15.4 10.7004 14.6 9.90039"/>
      <path d="M10.1 7.09961C9.00001 7.19961 7.70001 7.69961 6.00001 8.59961C2.50001 10.5996 1.30001 12.4996 2.30001 14.1996C6.80001 21.9996 11.8 22.5996 13.5 21.5996C14.4 21.0996 15.4 19.4996 15.4 16.8996"/>
      <path d="M9.09998 16.5004C9.39998 15.4004 10.5 14.8004 11.5 15.1004"/>

    </svg>
  );
}
