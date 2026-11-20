import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ChevronsDownUpIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M7 20L12 15L17 20"/>
      <path d="M7 4L12 9L17 4"/>

    </svg>
  );
}
