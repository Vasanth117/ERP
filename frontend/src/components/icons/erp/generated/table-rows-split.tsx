import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function TableRowsSplitIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M14 10H16"/>
      <path d="M15 22V14"/>
      <path d="M15 2V6"/>
      <path d="M2 10H4"/>
      <path d="M20 10H22"/>
      <path d="M3 19H21"/>
      <path d="M3 22V16C3 15.7374 3.05173 15.4773 3.15224 15.2346C3.25275 14.992 3.40007 14.7715 3.58579 14.5858C3.7715 14.4001 3.99198 14.2528 4.23463 14.1522C4.47728 14.0517 4.73736 14 5 14H19C19.2626 14 19.5227 14.0517 19.7654 14.1522C20.008 14.2528 20.2285 14.4001 20.4142 14.5858C20.5999 14.7715 20.7472 14.992 20.8478 15.2346C20.9483 15.4773 21 15.7374 21 16V22"/>
      <path d="M3 2V4C3 4.53043 3.21071 5.03914 3.58579 5.41421C3.96086 5.78929 4.46957 6 5 6H19C19.5304 6 20.0391 5.78929 20.4142 5.41421C20.7893 5.03914 21 4.53043 21 4V2"/>
      <path d="M8 10H10"/>
      <path d="M9 22V14"/>
      <path d="M9 2V6"/>

    </svg>
  );
}
