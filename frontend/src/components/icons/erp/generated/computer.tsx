import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ComputerIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M7 2H17C17.5304 2 18.0391 2.21071 18.4142 2.58579C18.7893 2.96086 19 3.46957 19 4V8C19 8.53043 18.7893 9.03914 18.4142 9.41421C18.0391 9.78929 17.5304 10 17 10H7C6.46957 10 5.96086 9.78929 5.58579 9.41421C5.21071 9.03914 5 8.53043 5 8V4C5 3.46957 5.21071 2.96086 5.58579 2.58579C5.96086 2.21071 6.46957 2 7 2Z"/>
      <path d="M4 14H20C20.5304 14 21.0391 14.2107 21.4142 14.5858C21.7893 14.9609 22 15.4696 22 16V20C22 20.5304 21.7893 21.0391 21.4142 21.4142C21.0391 21.7893 20.5304 22 20 22H4C3.46957 22 2.96086 21.7893 2.58579 21.4142C2.21071 21.0391 2 20.5304 2 20V16C2 15.4696 2.21071 14.9609 2.58579 14.5858C2.96086 14.2107 3.46957 14 4 14Z"/>
      <path d="M6 18H8"/>
      <path d="M12 18H18"/>

    </svg>
  );
}
