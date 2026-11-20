import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function BusFrontIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M4 6L2 7"/>
      <path d="M10 6H14"/>
      <path d="M22 7L20 6"/>
      <path d="M6 3H18C18.5304 3 19.0391 3.21071 19.4142 3.58579C19.7893 3.96086 20 4.46957 20 5V17C20 17.5304 19.7893 18.0391 19.4142 18.4142C19.0391 18.7893 18.5304 19 18 19H6C5.46957 19 4.96086 18.7893 4.58579 18.4142C4.21071 18.0391 4 17.5304 4 17V5C4 4.46957 4.21071 3.96086 4.58579 3.58579C4.96086 3.21071 5.46957 3 6 3Z"/>
      <path d="M4 11H20"/>
      <path d="M8 15H8.01"/>
      <path d="M16 15H16.01"/>
      <path d="M6 19V21"/>
      <path d="M18 21V19"/>

    </svg>
  );
}
