import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ListVideoIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M12 12H3"/>
      <path d="M16 6H3"/>
      <path d="M12 18H3"/>
      <path d="M16 12L21 15L16 18V12Z"/>

    </svg>
  );
}
