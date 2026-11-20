import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function LoaderIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M12 2V6"/>
      <path d="M16.2 7.80039L19.1 4.90039"/>
      <path d="M18 12H22"/>
      <path d="M16.2 16.2002L19.1 19.1002"/>
      <path d="M12 18V22"/>
      <path d="M4.89999 19.1002L7.79999 16.2002"/>
      <path d="M2 12H6"/>
      <path d="M4.89999 4.90039L7.79999 7.80039"/>

    </svg>
  );
}
