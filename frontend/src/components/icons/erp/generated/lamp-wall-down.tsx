import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function LampWallDownIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M11 13H17L20 20H8L11 13Z"/>
      <path d="M14 13V8C14 7.46957 13.7893 6.96086 13.4142 6.58579C13.0391 6.21071 12.5304 6 12 6H8"/>
      <path d="M4 9H6C6.53043 9 7.03914 8.78929 7.41421 8.41421C7.78929 8.03914 8 7.53043 8 7V5C8 4.46957 7.78929 3.96086 7.41421 3.58579C7.03914 3.21071 6.53043 3 6 3H4V9Z"/>

    </svg>
  );
}
