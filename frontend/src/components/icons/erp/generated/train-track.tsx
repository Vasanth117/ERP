import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function TrainTrackIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M2 17L17 2"/>
      <path d="M2 14L10 22"/>
      <path d="M5 11L13 19"/>
      <path d="M8 8L16 16"/>
      <path d="M11 5L19 13"/>
      <path d="M14 2L22 10"/>
      <path d="M7 22L22 7"/>

    </svg>
  );
}
