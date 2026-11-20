import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function FileImageIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M15 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V20C4 20.5304 4.21071 21.0391 4.58579 21.4142C4.96086 21.7893 5.46957 22 6 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V7L15 2Z"/>
      <path d="M14 2V6C14 6.53043 14.2107 7.03914 14.5858 7.41421C14.9609 7.78929 15.4696 8 16 8H20"/>
      <path d="M8 12C8 12.5304 8.21071 13.0391 8.58579 13.4142C8.96086 13.7893 9.46957 14 10 14C10.5304 14 11.0391 13.7893 11.4142 13.4142C11.7893 13.0391 12 12.5304 12 12C12 11.4696 11.7893 10.9609 11.4142 10.5858C11.0391 10.2107 10.5304 10 10 10C9.46957 10 8.96086 10.2107 8.58579 10.5858C8.21071 10.9609 8 11.4696 8 12Z"/>
      <path d="M20 17L18.704 15.704C18.252 15.2522 17.6391 14.9983 17 14.9983C16.3609 14.9983 15.748 15.2522 15.296 15.704L9 22"/>

    </svg>
  );
}
