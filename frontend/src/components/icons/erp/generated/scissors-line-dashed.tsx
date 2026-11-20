import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ScissorsLineDashedIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M5.42004 9.41992L8.00004 11.9999"/>
      <path d="M2 8C2 8.53043 2.21071 9.03914 2.58579 9.41421C2.96086 9.78929 3.46957 10 4 10C4.53043 10 5.03914 9.78929 5.41421 9.41421C5.78929 9.03914 6 8.53043 6 8C6 7.46957 5.78929 6.96086 5.41421 6.58579C5.03914 6.21071 4.53043 6 4 6C3.46957 6 2.96086 6.21071 2.58579 6.58579C2.21071 6.96086 2 7.46957 2 8Z"/>
      <path d="M14 6L5.42004 14.58"/>
      <path d="M2 16C2 16.5304 2.21071 17.0391 2.58579 17.4142C2.96086 17.7893 3.46957 18 4 18C4.53043 18 5.03914 17.7893 5.41421 17.4142C5.78929 17.0391 6 16.5304 6 16C6 15.4696 5.78929 14.9609 5.41421 14.5858C5.03914 14.2107 4.53043 14 4 14C3.46957 14 2.96086 14.2107 2.58579 14.5858C2.21071 14.9609 2 15.4696 2 16Z"/>
      <path d="M10.8 14.7998L14 17.9998"/>
      <path d="M16 12H14"/>
      <path d="M22 12H20"/>

    </svg>
  );
}
