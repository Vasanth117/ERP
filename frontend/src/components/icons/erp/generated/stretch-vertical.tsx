import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function StretchVerticalIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M6 2H8C8.53043 2 9.03914 2.21071 9.41421 2.58579C9.78929 2.96086 10 3.46957 10 4V20C10 20.5304 9.78929 21.0391 9.41421 21.4142C9.03914 21.7893 8.53043 22 8 22H6C5.46957 22 4.96086 21.7893 4.58579 21.4142C4.21071 21.0391 4 20.5304 4 20V4C4 3.46957 4.21071 2.96086 4.58579 2.58579C4.96086 2.21071 5.46957 2 6 2Z"/>
      <path d="M16 2H18C18.5304 2 19.0391 2.21071 19.4142 2.58579C19.7893 2.96086 20 3.46957 20 4V20C20 20.5304 19.7893 21.0391 19.4142 21.4142C19.0391 21.7893 18.5304 22 18 22H16C15.4696 22 14.9609 21.7893 14.5858 21.4142C14.2107 21.0391 14 20.5304 14 20V4C14 3.46957 14.2107 2.96086 14.5858 2.58579C14.9609 2.21071 15.4696 2 16 2Z"/>

    </svg>
  );
}
