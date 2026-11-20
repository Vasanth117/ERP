import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function PictureInPicture2Icon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M21 9V6C21 5.46957 20.7893 4.96086 20.4142 4.58579C20.0391 4.21071 19.5304 4 19 4H4C3.46957 4 2.96086 4.21071 2.58579 4.58579C2.21071 4.96086 2 5.46957 2 6V16C2 17.1 2.9 18 4 18H8"/>
      <path d="M14 13H20C20.5304 13 21.0391 13.2107 21.4142 13.5858C21.7893 13.9609 22 14.4696 22 15V18C22 18.5304 21.7893 19.0391 21.4142 19.4142C21.0391 19.7893 20.5304 20 20 20H14C13.4696 20 12.9609 19.7893 12.5858 19.4142C12.2107 19.0391 12 18.5304 12 18V15C12 14.4696 12.2107 13.9609 12.5858 13.5858C12.9609 13.2107 13.4696 13 14 13Z"/>

    </svg>
  );
}
