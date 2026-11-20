import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function AlignEndHorizontalIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M6 2H8C8.53043 2 9.03914 2.21071 9.41421 2.58579C9.78929 2.96086 10 3.46957 10 4V16C10 16.5304 9.78929 17.0391 9.41421 17.4142C9.03914 17.7893 8.53043 18 8 18H6C5.46957 18 4.96086 17.7893 4.58579 17.4142C4.21071 17.0391 4 16.5304 4 16V4C4 3.46957 4.21071 2.96086 4.58579 2.58579C4.96086 2.21071 5.46957 2 6 2Z"/>
      <path d="M16 9H18C18.5304 9 19.0391 9.21071 19.4142 9.58579C19.7893 9.96086 20 10.4696 20 11V16C20 16.5304 19.7893 17.0391 19.4142 17.4142C19.0391 17.7893 18.5304 18 18 18H16C15.4696 18 14.9609 17.7893 14.5858 17.4142C14.2107 17.0391 14 16.5304 14 16V11C14 10.4696 14.2107 9.96086 14.5858 9.58579C14.9609 9.21071 15.4696 9 16 9Z"/>
      <path d="M22 22H2"/>

    </svg>
  );
}
