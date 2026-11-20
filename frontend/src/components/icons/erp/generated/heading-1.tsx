import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function Heading1Icon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M4 12H12"/>
      <path d="M4 18V6"/>
      <path d="M12 18V6"/>
      <path d="M17 12L20 10V18"/>

    </svg>
  );
}
