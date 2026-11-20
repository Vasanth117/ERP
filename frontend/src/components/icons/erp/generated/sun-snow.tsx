import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function SunSnowIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M10 9C9.20435 9 8.44129 9.31607 7.87868 9.87868C7.31607 10.4413 7 11.2044 7 12C7 12.7956 7.31607 13.5587 7.87868 14.1213C8.44129 14.6839 9.20435 15 10 15"/>
      <path d="M2 12H3"/>
      <path d="M14 21V3"/>
      <path d="M10 4V3"/>
      <path d="M10 21V20"/>
      <path d="M3.64001 18.3602L4.34001 17.6602"/>
      <path d="M4.34001 6.33965L3.64001 5.63965"/>
      <path d="M14 12H22"/>
      <path d="M17 4L14 7"/>
      <path d="M14 17L17 20"/>
      <path d="M21 15L18 12L21 9"/>

    </svg>
  );
}
