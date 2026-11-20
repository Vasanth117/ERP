import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function FoldVerticalIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M12 22V16"/>
      <path d="M12 8V2"/>
      <path d="M4 12H2"/>
      <path d="M10 12H8"/>
      <path d="M16 12H14"/>
      <path d="M22 12H20"/>
      <path d="M15 19L12 16L9 19"/>
      <path d="M15 5L12 8L9 5"/>

    </svg>
  );
}
