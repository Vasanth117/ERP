import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function BuildingIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M9 22V18H15V22"/>
      <path d="M8 6H8.01"/>
      <path d="M16 6H16.01"/>
      <path d="M12 6H12.01"/>
      <path d="M12 10H12.01"/>
      <path d="M12 14H12.01"/>
      <path d="M16 10H16.01"/>
      <path d="M16 14H16.01"/>
      <path d="M8 10H8.01"/>
      <path d="M8 14H8.01"/>

    </svg>
  );
}
