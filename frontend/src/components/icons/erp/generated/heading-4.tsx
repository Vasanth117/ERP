import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function Heading4Icon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M12 18V6"/>
      <path d="M17 10V13C17 13.2652 17.1054 13.5196 17.2929 13.7071C17.4804 13.8946 17.7348 14 18 14H21"/>
      <path d="M21 10V18"/>
      <path d="M4 12H12"/>
      <path d="M4 18V6"/>

    </svg>
  );
}
