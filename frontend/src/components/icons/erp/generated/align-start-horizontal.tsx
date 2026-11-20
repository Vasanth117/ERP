import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function AlignStartHorizontalIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M6 6H8C8.53043 6 9.03914 6.21071 9.41421 6.58579C9.78929 6.96086 10 7.46957 10 8V20C10 20.5304 9.78929 21.0391 9.41421 21.4142C9.03914 21.7893 8.53043 22 8 22H6C5.46957 22 4.96086 21.7893 4.58579 21.4142C4.21071 21.0391 4 20.5304 4 20V8C4 7.46957 4.21071 6.96086 4.58579 6.58579C4.96086 6.21071 5.46957 6 6 6Z"/>
      <path d="M16 6H18C18.5304 6 19.0391 6.21071 19.4142 6.58579C19.7893 6.96086 20 7.46957 20 8V13C20 13.5304 19.7893 14.0391 19.4142 14.4142C19.0391 14.7893 18.5304 15 18 15H16C15.4696 15 14.9609 14.7893 14.5858 14.4142C14.2107 14.0391 14 13.5304 14 13V8C14 7.46957 14.2107 6.96086 14.5858 6.58579C14.9609 6.21071 15.4696 6 16 6Z"/>
      <path d="M22 2H2"/>

    </svg>
  );
}
