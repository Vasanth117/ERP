import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function PilcrowLeftIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M14 3V14"/>
      <path d="M14 9H11C10.2044 9 9.44129 8.68393 8.87868 8.12132C8.31607 7.55871 8 6.79565 8 6C8 5.20435 8.31607 4.44129 8.87868 3.87868C9.44129 3.31607 10.2044 3 11 3H20"/>
      <path d="M18 3V14"/>
      <path d="M22 18H2L6 14"/>
      <path d="M6 22L2 18"/>

    </svg>
  );
}
