import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function RussianRubleIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M6 11H14C15.0609 11 16.0783 10.5786 16.8284 9.82843C17.5786 9.07828 18 8.06087 18 7C18 5.93913 17.5786 4.92172 16.8284 4.17157C16.0783 3.42143 15.0609 3 14 3H9V21"/>
      <path d="M6 15H14"/>

    </svg>
  );
}
