import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function CaseSensitiveIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M3 15L7 7L11 15"/>
      <path d="M4 13H10"/>
      <path d="M15 12C15 12.7956 15.3161 13.5587 15.8787 14.1213C16.4413 14.6839 17.2044 15 18 15C18.7956 15 19.5587 14.6839 20.1213 14.1213C20.6839 13.5587 21 12.7956 21 12C21 11.2044 20.6839 10.4413 20.1213 9.87868C19.5587 9.31607 18.7956 9 18 9C17.2044 9 16.4413 9.31607 15.8787 9.87868C15.3161 10.4413 15 11.2044 15 12Z"/>
      <path d="M21 9V15"/>

    </svg>
  );
}
