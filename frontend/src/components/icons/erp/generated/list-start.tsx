import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ListStartIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M16 18H3"/>
      <path d="M10 6H3"/>
      <path d="M21 18V8C21 7.46957 20.7893 6.96086 20.4142 6.58579C20.0391 6.21071 19.5304 6 19 6H14"/>
      <path d="M16 8L14 6L16 4"/>

    </svg>
  );
}
