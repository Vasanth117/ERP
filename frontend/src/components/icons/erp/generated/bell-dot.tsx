import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function BellDotIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M19.4 14.9C20.2 16.4 21 17 21 17H3C3 17 6 15 6 8C6 4.7 8.7 2 12 2C12.7 2 13.3 2.1 13.9 2.3"/>
      <path d="M10.3 21C10.4674 21.3044 10.7134 21.5583 11.0125 21.7352C11.3115 21.912 11.6526 22.0053 12 22.0053C12.3474 22.0053 12.6885 21.912 12.9875 21.7352C13.2865 21.5583 13.5326 21.3044 13.7 21"/>
      <path d="M15 8C15 8.79565 15.3161 9.55871 15.8787 10.1213C16.4413 10.6839 17.2044 11 18 11C18.7956 11 19.5587 10.6839 20.1213 10.1213C20.6839 9.55871 21 8.79565 21 8C21 7.20435 20.6839 6.44129 20.1213 5.87868C19.5587 5.31607 18.7956 5 18 5C17.2044 5 16.4413 5.31607 15.8787 5.87868C15.3161 6.44129 15 7.20435 15 8Z"/>

    </svg>
  );
}
