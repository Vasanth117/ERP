import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function AlignVerticalDistributeCenterIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M22 17H19"/>
      <path d="M22 7H17"/>
      <path d="M5 17H2"/>
      <path d="M7 7H2"/>
      <path d="M7 14H17C17.5304 14 18.0391 14.2107 18.4142 14.5858C18.7893 14.9609 19 15.4696 19 16V18C19 18.5304 18.7893 19.0391 18.4142 19.4142C18.0391 19.7893 17.5304 20 17 20H7C6.46957 20 5.96086 19.7893 5.58579 19.4142C5.21071 19.0391 5 18.5304 5 18V16C5 15.4696 5.21071 14.9609 5.58579 14.5858C5.96086 14.2107 6.46957 14 7 14Z"/>
      <path d="M9 4H15C15.5304 4 16.0391 4.21071 16.4142 4.58579C16.7893 4.96086 17 5.46957 17 6V8C17 8.53043 16.7893 9.03914 16.4142 9.41421C16.0391 9.78929 15.5304 10 15 10H9C8.46957 10 7.96086 9.78929 7.58579 9.41421C7.21071 9.03914 7 8.53043 7 8V6C7 5.46957 7.21071 4.96086 7.58579 4.58579C7.96086 4.21071 8.46957 4 9 4Z"/>

    </svg>
  );
}
