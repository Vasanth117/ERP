import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function AlignVerticalSpaceAroundIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M9 9H15C15.5304 9 16.0391 9.21071 16.4142 9.58579C16.7893 9.96086 17 10.4696 17 11V13C17 13.5304 16.7893 14.0391 16.4142 14.4142C16.0391 14.7893 15.5304 15 15 15H9C8.46957 15 7.96086 14.7893 7.58579 14.4142C7.21071 14.0391 7 13.5304 7 13V11C7 10.4696 7.21071 9.96086 7.58579 9.58579C7.96086 9.21071 8.46957 9 9 9Z"/>
      <path d="M22 20H2"/>
      <path d="M22 4H2"/>

    </svg>
  );
}
