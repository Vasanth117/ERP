import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ListPlusIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M11 12H3"/>
      <path d="M16 6H3"/>
      <path d="M16 18H3"/>
      <path d="M18 9V15"/>
      <path d="M21 12H15"/>

    </svg>
  );
}
