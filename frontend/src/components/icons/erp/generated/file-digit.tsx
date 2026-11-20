import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function FileDigitIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M4 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V7L15 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V8"/>
      <path d="M14 2V6C14 6.53043 14.2107 7.03914 14.5858 7.41421C14.9609 7.78929 15.4696 8 16 8H20"/>
      <path d="M4 12C4.53043 12 5.03914 12.2107 5.41421 12.5858C5.78929 12.9609 6 13.4696 6 14V16C6 16.5304 5.78929 17.0391 5.41421 17.4142C5.03914 17.7893 4.53043 18 4 18C3.46957 18 2.96086 17.7893 2.58579 17.4142C2.21071 17.0391 2 16.5304 2 16V14C2 13.4696 2.21071 12.9609 2.58579 12.5858C2.96086 12.2107 3.46957 12 4 12Z"/>
      <path d="M10 12H12V18"/>
      <path d="M10 18H14"/>

    </svg>
  );
}
