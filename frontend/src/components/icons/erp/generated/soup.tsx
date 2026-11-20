import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function SoupIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M12 21C14.3869 21 16.6761 20.0518 18.364 18.364C20.0518 16.6761 21 14.3869 21 12H3C3 14.3869 3.94821 16.6761 5.63604 18.364C7.32387 20.0518 9.61305 21 12 21Z"/>
      <path d="M7 21H17"/>
      <path d="M19.5 12L22 6"/>
      <path d="M16.25 3C16.52 3.1 17.05 3.53 17 4.36C16.94 5.19 16.07 5.56 16 6.38C15.95 7.16 16.34 7.62 16.73 8"/>
      <path d="M11.25 3C11.52 3.1 12.05 3.53 11.99 4.36C11.94 5.19 11.06 5.56 11.01 6.38C10.95 7.16 11.34 7.62 11.73 8"/>
      <path d="M6.25001 3C6.52001 3.1 7.05001 3.53 7.00001 4.36C6.94001 5.19 6.07001 5.56 6.00001 6.38C5.95001 7.16 6.34001 7.62 6.74001 8"/>

    </svg>
  );
}
