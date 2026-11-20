import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function FileStackIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M21 7H18C17.4696 7 16.9609 6.78929 16.5858 6.41421C16.2107 6.03914 16 5.53043 16 5V2"/>
      <path d="M21 6V12.5C21 13.3 20.3 14 19.5 14H12.5C11.7 14 11 13.3 11 12.5V3.5C11 2.7 11.7 2 12.5 2H17L21 6Z"/>
      <path d="M7 8V16.8C7 17.1 7.2 17.4 7.4 17.6C7.6 17.8 7.9 18 8.2 18H15"/>
      <path d="M3 12V20.8C3 21.1 3.2 21.4 3.4 21.6C3.6 21.8 3.9 22 4.2 22H11"/>

    </svg>
  );
}
