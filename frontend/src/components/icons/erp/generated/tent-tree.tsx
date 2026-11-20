import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function TentTreeIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M2 4C2 4.53043 2.21071 5.03914 2.58579 5.41421C2.96086 5.78929 3.46957 6 4 6C4.53043 6 5.03914 5.78929 5.41421 5.41421C5.78929 5.03914 6 4.53043 6 4C6 3.46957 5.78929 2.96086 5.41421 2.58579C5.03914 2.21071 4.53043 2 4 2C3.46957 2 2.96086 2.21071 2.58579 2.58579C2.21071 2.96086 2 3.46957 2 4Z"/>
      <path d="M14 5L17 2L20 5"/>
      <path d="M14 10L17 7L20 10"/>
      <path d="M17 14V2"/>
      <path d="M17 14H7L2 22H22L17 14Z"/>
      <path d="M8 14V22"/>
      <path d="M9 14L14 22"/>

    </svg>
  );
}
