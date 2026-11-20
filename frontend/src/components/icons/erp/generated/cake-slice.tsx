import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function CakeSliceIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M7 7C7 7.53043 7.21071 8.03914 7.58579 8.41421C7.96086 8.78929 8.46957 9 9 9C9.53043 9 10.0391 8.78929 10.4142 8.41421C10.7893 8.03914 11 7.53043 11 7C11 6.46957 10.7893 5.96086 10.4142 5.58579C10.0391 5.21071 9.53043 5 9 5C8.46957 5 7.96086 5.21071 7.58579 5.58579C7.21071 5.96086 7 6.46957 7 7Z"/>
      <path d="M7.2 7.9L3 11V20C3 20.6 3.4 21 4 21H20C20.6 21 21 20.6 21 20V11C21 9 18 5 14 3L10.4 5.6"/>
      <path d="M16 13H3"/>
      <path d="M16 17H3"/>

    </svg>
  );
}
