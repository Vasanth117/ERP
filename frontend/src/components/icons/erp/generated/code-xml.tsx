import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function CodeXmlIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M18 16L22 12L18 8"/>
      <path d="M6 8L2 12L6 16"/>
      <path d="M14.5 4L9.5 20"/>

    </svg>
  );
}
