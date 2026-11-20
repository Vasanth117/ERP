import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function VoicemailIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M2 12C2 13.0609 2.42143 14.0783 3.17157 14.8284C3.92172 15.5786 4.93913 16 6 16C7.06087 16 8.07828 15.5786 8.82843 14.8284C9.57857 14.0783 10 13.0609 10 12C10 10.9391 9.57857 9.92172 8.82843 9.17157C8.07828 8.42143 7.06087 8 6 8C4.93913 8 3.92172 8.42143 3.17157 9.17157C2.42143 9.92172 2 10.9391 2 12Z"/>
      <path d="M14 12C14 13.0609 14.4214 14.0783 15.1716 14.8284C15.9217 15.5786 16.9391 16 18 16C19.0609 16 20.0783 15.5786 20.8284 14.8284C21.5786 14.0783 22 13.0609 22 12C22 10.9391 21.5786 9.92172 20.8284 9.17157C20.0783 8.42143 19.0609 8 18 8C16.9391 8 15.9217 8.42143 15.1716 9.17157C14.4214 9.92172 14 10.9391 14 12Z"/>
      <path d="M6 16H18"/>

    </svg>
  );
}
