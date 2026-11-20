import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function LampWallUpIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M11 4H17L20 11H8L11 4Z"/>
      <path d="M14 11V16C14 16.5304 13.7893 17.0391 13.4142 17.4142C13.0391 17.7893 12.5304 18 12 18H8"/>
      <path d="M4 15H6C6.53043 15 7.03914 15.2107 7.41421 15.5858C7.78929 15.9609 8 16.4696 8 17V19C8 19.5304 7.78929 20.0391 7.41421 20.4142C7.03914 20.7893 6.53043 21 6 21H4V15Z"/>

    </svg>
  );
}
