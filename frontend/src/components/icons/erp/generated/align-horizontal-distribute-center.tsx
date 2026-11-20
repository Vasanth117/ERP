import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function AlignHorizontalDistributeCenterIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M6 5H8C8.53043 5 9.03914 5.21071 9.41421 5.58579C9.78929 5.96086 10 6.46957 10 7V17C10 17.5304 9.78929 18.0391 9.41421 18.4142C9.03914 18.7893 8.53043 19 8 19H6C5.46957 19 4.96086 18.7893 4.58579 18.4142C4.21071 18.0391 4 17.5304 4 17V7C4 6.46957 4.21071 5.96086 4.58579 5.58579C4.96086 5.21071 5.46957 5 6 5Z"/>
      <path d="M16 7H18C18.5304 7 19.0391 7.21071 19.4142 7.58579C19.7893 7.96086 20 8.46957 20 9V15C20 15.5304 19.7893 16.0391 19.4142 16.4142C19.0391 16.7893 18.5304 17 18 17H16C15.4696 17 14.9609 16.7893 14.5858 16.4142C14.2107 16.0391 14 15.5304 14 15V9C14 8.46957 14.2107 7.96086 14.5858 7.58579C14.9609 7.21071 15.4696 7 16 7Z"/>
      <path d="M17 22V17"/>
      <path d="M17 7V2"/>
      <path d="M7 22V19"/>
      <path d="M7 5V2"/>

    </svg>
  );
}
