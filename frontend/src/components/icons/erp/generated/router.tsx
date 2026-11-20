import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function RouterIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M4 14H20C20.5304 14 21.0391 14.2107 21.4142 14.5858C21.7893 14.9609 22 15.4696 22 16V20C22 20.5304 21.7893 21.0391 21.4142 21.4142C21.0391 21.7893 20.5304 22 20 22H4C3.46957 22 2.96086 21.7893 2.58579 21.4142C2.21071 21.0391 2 20.5304 2 20V16C2 15.4696 2.21071 14.9609 2.58579 14.5858C2.96086 14.2107 3.46957 14 4 14Z"/>
      <path d="M6.01 18H6"/>
      <path d="M10.01 18H10"/>
      <path d="M15 10V14"/>
      <path d="M17.8401 7.17022C17.4686 6.79831 17.0274 6.50328 16.5418 6.30198C16.0562 6.10068 15.5357 5.99707 15.0101 5.99707C14.4844 5.99707 13.9639 6.10068 13.4783 6.30198C12.9927 6.50328 12.5515 6.79831 12.1801 7.17022"/>
      <path d="M20.66 4.33983C19.1598 2.84067 17.1258 1.99854 15.005 1.99854C12.8842 1.99854 10.8501 2.84067 9.34998 4.33983"/>

    </svg>
  );
}
