import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function AlignHorizontalJustifyCenterIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M4 5H6C6.53043 5 7.03914 5.21071 7.41421 5.58579C7.78929 5.96086 8 6.46957 8 7V17C8 17.5304 7.78929 18.0391 7.41421 18.4142C7.03914 18.7893 6.53043 19 6 19H4C3.46957 19 2.96086 18.7893 2.58579 18.4142C2.21071 18.0391 2 17.5304 2 17V7C2 6.46957 2.21071 5.96086 2.58579 5.58579C2.96086 5.21071 3.46957 5 4 5Z"/>
      <path d="M18 7H20C20.5304 7 21.0391 7.21071 21.4142 7.58579C21.7893 7.96086 22 8.46957 22 9V15C22 15.5304 21.7893 16.0391 21.4142 16.4142C21.0391 16.7893 20.5304 17 20 17H18C17.4696 17 16.9609 16.7893 16.5858 16.4142C16.2107 16.0391 16 15.5304 16 15V9C16 8.46957 16.2107 7.96086 16.5858 7.58579C16.9609 7.21071 17.4696 7 18 7Z"/>
      <path d="M12 2V22"/>

    </svg>
  );
}
