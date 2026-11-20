import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function FishSymbolIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M2 15.9997C2 15.9997 11 0.999684 22 11.9997C11 22.9997 2 7.99968 2 7.99968"/>

    </svg>
  );
}
