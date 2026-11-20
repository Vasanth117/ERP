import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function PilcrowRightIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M10 3V14"/>
      <path d="M10 9H7C6.20435 9 5.44129 8.68393 4.87868 8.12132C4.31607 7.55871 4 6.79565 4 6C4 5.20435 4.31607 4.44129 4.87868 3.87868C5.44129 3.31607 6.20435 3 7 3H15"/>
      <path d="M14 3V14"/>
      <path d="M18 14L22 18H2"/>
      <path d="M22 18L18 22"/>

    </svg>
  );
}
