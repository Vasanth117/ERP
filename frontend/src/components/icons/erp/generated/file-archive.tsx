import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function FileArchiveIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M10 12V11"/>
      <path d="M10 18V16"/>
      <path d="M10 7V6"/>
      <path d="M14 2V6C14 6.53043 14.2107 7.03914 14.5858 7.41421C14.9609 7.78929 15.4696 8 16 8H20"/>
      <path d="M15.5 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V7L15 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V20C4.00007 20.355 4.09464 20.7036 4.274 21.01"/>
      <path d="M8 20C8 20.5304 8.21071 21.0391 8.58579 21.4142C8.96086 21.7893 9.46957 22 10 22C10.5304 22 11.0391 21.7893 11.4142 21.4142C11.7893 21.0391 12 20.5304 12 20C12 19.4696 11.7893 18.9609 11.4142 18.5858C11.0391 18.2107 10.5304 18 10 18C9.46957 18 8.96086 18.2107 8.58579 18.5858C8.21071 18.9609 8 19.4696 8 20Z"/>

    </svg>
  );
}
