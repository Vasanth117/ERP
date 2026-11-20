import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function LandmarkIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M3 22H21"/>
      <path d="M6 18V11"/>
      <path d="M10 18V11"/>
      <path d="M14 18V11"/>
      <path d="M18 18V11"/>
      <path d="M12 2L20 7H4L12 2Z"/>

    </svg>
  );
}
