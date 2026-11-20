import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function SpeakerIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M6 2H18C18.5304 2 19.0391 2.21071 19.4142 2.58579C19.7893 2.96086 20 3.46957 20 4V20C20 20.5304 19.7893 21.0391 19.4142 21.4142C19.0391 21.7893 18.5304 22 18 22H6C5.46957 22 4.96086 21.7893 4.58579 21.4142C4.21071 21.0391 4 20.5304 4 20V4C4 3.46957 4.21071 2.96086 4.58579 2.58579C4.96086 2.21071 5.46957 2 6 2Z"/>
      <path d="M12 6H12.01"/>
      <path d="M8 14C8 15.0609 8.42143 16.0783 9.17157 16.8284C9.92172 17.5786 10.9391 18 12 18C13.0609 18 14.0783 17.5786 14.8284 16.8284C15.5786 16.0783 16 15.0609 16 14C16 12.9391 15.5786 11.9217 14.8284 11.1716C14.0783 10.4214 13.0609 10 12 10C10.9391 10 9.92172 10.4214 9.17157 11.1716C8.42143 11.9217 8 12.9391 8 14Z"/>
      <path d="M12 14H12.01"/>

    </svg>
  );
}
