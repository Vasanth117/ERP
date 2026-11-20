import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ImageUpIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M10.3 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V5C3 4.46957 3.21071 3.96086 3.58579 3.58579C3.96086 3.21071 4.46957 3 5 3H19C19.5304 3 20.0391 3.21071 20.4142 3.58579C20.7893 3.96086 21 4.46957 21 5V15L17.9 11.9C17.5237 11.5312 17.017 11.3258 16.4901 11.3284C15.9632 11.331 15.4586 11.5415 15.086 11.914L6 21"/>
      <path d="M14 19.5L17 16.5L20 19.5"/>
      <path d="M17 22V16.5"/>
      <path d="M7 9C7 9.53043 7.21071 10.0391 7.58579 10.4142C7.96086 10.7893 8.46957 11 9 11C9.53043 11 10.0391 10.7893 10.4142 10.4142C10.7893 10.0391 11 9.53043 11 9C11 8.46957 10.7893 7.96086 10.4142 7.58579C10.0391 7.21071 9.53043 7 9 7C8.46957 7 7.96086 7.21071 7.58579 7.58579C7.21071 7.96086 7 8.46957 7 9Z"/>

    </svg>
  );
}
