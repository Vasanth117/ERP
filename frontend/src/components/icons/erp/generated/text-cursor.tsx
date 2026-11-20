import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function TextCursorIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M17 22H16C14.9391 22 13.9217 21.5786 13.1716 20.8284C12.4214 20.0783 12 19.0609 12 18V6C12 4.93913 12.4214 3.92172 13.1716 3.17157C13.9217 2.42143 14.9391 2 16 2H17"/>
      <path d="M7 22H8C9.06087 22 10.0783 21.5786 10.8284 20.8284C11.5786 20.0783 12 19.0609 12 18V17"/>
      <path d="M7 2H8C9.06087 2 10.0783 2.42143 10.8284 3.17157C11.5786 3.92172 12 4.93913 12 6V7"/>

    </svg>
  );
}
