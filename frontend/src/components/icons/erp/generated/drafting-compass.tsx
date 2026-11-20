import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function DraftingCompassIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M12.99 6.74023L14.92 10.1802"/>
      <path d="M19.136 12C18.2051 12.948 17.0947 13.7011 15.8696 14.2151C14.6444 14.7292 13.3291 14.994 12.0005 14.994C10.6719 14.994 9.35656 14.7292 8.13141 14.2151C6.90626 13.7011 5.79583 12.948 4.86499 12"/>
      <path d="M21 21.0002L18.84 17.1602"/>
      <path d="M3 21.0002L11.02 6.74023"/>
      <path d="M10 5C10 5.53043 10.2107 6.03914 10.5858 6.41421C10.9609 6.78929 11.4696 7 12 7C12.5304 7 13.0391 6.78929 13.4142 6.41421C13.7893 6.03914 14 5.53043 14 5C14 4.46957 13.7893 3.96086 13.4142 3.58579C13.0391 3.21071 12.5304 3 12 3C11.4696 3 10.9609 3.21071 10.5858 3.58579C10.2107 3.96086 10 4.46957 10 5Z"/>

    </svg>
  );
}
