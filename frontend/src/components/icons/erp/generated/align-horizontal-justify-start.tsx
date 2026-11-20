import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function AlignHorizontalJustifyStartIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M8 5H10C10.5304 5 11.0391 5.21071 11.4142 5.58579C11.7893 5.96086 12 6.46957 12 7V17C12 17.5304 11.7893 18.0391 11.4142 18.4142C11.0391 18.7893 10.5304 19 10 19H8C7.46957 19 6.96086 18.7893 6.58579 18.4142C6.21071 18.0391 6 17.5304 6 17V7C6 6.46957 6.21071 5.96086 6.58579 5.58579C6.96086 5.21071 7.46957 5 8 5Z"/>
      <path d="M18 7H20C20.5304 7 21.0391 7.21071 21.4142 7.58579C21.7893 7.96086 22 8.46957 22 9V15C22 15.5304 21.7893 16.0391 21.4142 16.4142C21.0391 16.7893 20.5304 17 20 17H18C17.4696 17 16.9609 16.7893 16.5858 16.4142C16.2107 16.0391 16 15.5304 16 15V9C16 8.46957 16.2107 7.96086 16.5858 7.58579C16.9609 7.21071 17.4696 7 18 7Z"/>
      <path d="M2 2V22"/>

    </svg>
  );
}
