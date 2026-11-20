import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function StickerIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M15.5 3H5C4.46957 3 3.96086 3.21071 3.58579 3.58579C3.21071 3.96086 3 4.46957 3 5V19C3 20.1 3.9 21 5 21H19C19.5304 21 20.0391 20.7893 20.4142 20.4142C20.7893 20.0391 21 19.5304 21 19V8.5L15.5 3Z"/>
      <path d="M14 3V7C14 7.53043 14.2107 8.03914 14.5858 8.41421C14.9609 8.78929 15.4696 9 16 9H20"/>
      <path d="M8 13H8.01"/>
      <path d="M16 13H16.01"/>
      <path d="M10 16C10 16 10.8 17 12 17C13.3 17 14 16 14 16"/>

    </svg>
  );
}
