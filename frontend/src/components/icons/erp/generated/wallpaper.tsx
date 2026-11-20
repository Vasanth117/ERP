import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function WallpaperIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M6 9C6 9.53043 6.21071 10.0391 6.58579 10.4142C6.96086 10.7893 7.46957 11 8 11C8.53043 11 9.03914 10.7893 9.41421 10.4142C9.78929 10.0391 10 9.53043 10 9C10 8.46957 9.78929 7.96086 9.41421 7.58579C9.03914 7.21071 8.53043 7 8 7C7.46957 7 6.96086 7.21071 6.58579 7.58579C6.21071 7.96086 6 8.46957 6 9Z"/>
      <path d="M9 17L15.1 10.9C15.4756 10.5319 15.9811 10.3265 16.5071 10.3284C17.033 10.3302 17.537 10.5392 17.91 10.91L22 15M9 17H4C3.46957 17 2.96086 16.7893 2.58579 16.4142C2.21071 16.0391 2 15.5304 2 15V5C2 4.46957 2.21071 3.96086 2.58579 3.58579C2.96086 3.21071 3.46957 3 4 3H20C20.5304 3 21.0391 3.21071 21.4142 3.58579C21.7893 3.96086 22 4.46957 22 5V15M9 17H20C20.5304 17 21.0391 16.7893 21.4142 16.4142C21.7893 16.0391 22 15.5304 22 15"/>
      <path d="M8 21H16"/>
      <path d="M12 17V21"/>

    </svg>
  );
}
