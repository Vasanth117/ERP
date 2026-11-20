import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function AlignVerticalJustifyEndIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M7 12H17C17.5304 12 18.0391 12.2107 18.4142 12.5858C18.7893 12.9609 19 13.4696 19 14V16C19 16.5304 18.7893 17.0391 18.4142 17.4142C18.0391 17.7893 17.5304 18 17 18H7C6.46957 18 5.96086 17.7893 5.58579 17.4142C5.21071 17.0391 5 16.5304 5 16V14C5 13.4696 5.21071 12.9609 5.58579 12.5858C5.96086 12.2107 6.46957 12 7 12Z"/>
      <path d="M9 2H15C15.5304 2 16.0391 2.21071 16.4142 2.58579C16.7893 2.96086 17 3.46957 17 4V6C17 6.53043 16.7893 7.03914 16.4142 7.41421C16.0391 7.78929 15.5304 8 15 8H9C8.46957 8 7.96086 7.78929 7.58579 7.41421C7.21071 7.03914 7 6.53043 7 6V4C7 3.46957 7.21071 2.96086 7.58579 2.58579C7.96086 2.21071 8.46957 2 9 2Z"/>
      <path d="M2 22H22"/>

    </svg>
  );
}
