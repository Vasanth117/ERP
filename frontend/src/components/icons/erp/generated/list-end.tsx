import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ListEndIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M16 12H3"/>
      <path d="M16 6H3"/>
      <path d="M10 18H3"/>
      <path d="M21 6V16C21 16.5304 20.7893 17.0391 20.4142 17.4142C20.0391 17.7893 19.5304 18 19 18H14"/>
      <path d="M16 16L14 18L16 20"/>

    </svg>
  );
}
