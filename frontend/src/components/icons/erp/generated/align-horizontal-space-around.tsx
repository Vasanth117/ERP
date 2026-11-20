import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function AlignHorizontalSpaceAroundIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M11 7H13C13.5304 7 14.0391 7.21071 14.4142 7.58579C14.7893 7.96086 15 8.46957 15 9V15C15 15.5304 14.7893 16.0391 14.4142 16.4142C14.0391 16.7893 13.5304 17 13 17H11C10.4696 17 9.96086 16.7893 9.58579 16.4142C9.21071 16.0391 9 15.5304 9 15V9C9 8.46957 9.21071 7.96086 9.58579 7.58579C9.96086 7.21071 10.4696 7 11 7Z"/>
      <path d="M4 22V2"/>
      <path d="M20 22V2"/>

    </svg>
  );
}
