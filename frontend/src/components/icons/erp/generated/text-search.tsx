import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function TextSearchIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M21 6H3"/>
      <path d="M10 12H3"/>
      <path d="M10 18H3"/>
      <path d="M14 15C14 15.7956 14.3161 16.5587 14.8787 17.1213C15.4413 17.6839 16.2044 18 17 18C17.7956 18 18.5587 17.6839 19.1213 17.1213C19.6839 16.5587 20 15.7956 20 15C20 14.2044 19.6839 13.4413 19.1213 12.8787C18.5587 12.3161 17.7956 12 17 12C16.2044 12 15.4413 12.3161 14.8787 12.8787C14.3161 13.4413 14 14.2044 14 15Z"/>
      <path d="M21 18.9996L19.1 17.0996"/>

    </svg>
  );
}
