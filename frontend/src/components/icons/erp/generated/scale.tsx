import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ScaleIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M16 16L19 8L22 16C21.13 16.65 20.08 17 19 17C17.92 17 16.87 16.65 16 16Z"/>
      <path d="M2 16L5 8L8 16C7.13 16.65 6.08 17 5 17C3.92 17 2.87 16.65 2 16Z"/>
      <path d="M7 21H17"/>
      <path d="M12 3V21"/>
      <path d="M3 7H5C7 7 10 6 12 5C14 6 17 7 19 7H21"/>

    </svg>
  );
}
