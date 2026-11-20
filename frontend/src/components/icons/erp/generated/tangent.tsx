import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function TangentIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M15 4C15 4.53043 15.2107 5.03914 15.5858 5.41421C15.9609 5.78929 16.4696 6 17 6C17.5304 6 18.0391 5.78929 18.4142 5.41421C18.7893 5.03914 19 4.53043 19 4C19 3.46957 18.7893 2.96086 18.4142 2.58579C18.0391 2.21071 17.5304 2 17 2C16.4696 2 15.9609 2.21071 15.5858 2.58579C15.2107 2.96086 15 3.46957 15 4Z"/>
      <path d="M15.59 5.41016L5.41 15.5902"/>
      <path d="M2 17C2 17.5304 2.21071 18.0391 2.58579 18.4142C2.96086 18.7893 3.46957 19 4 19C4.53043 19 5.03914 18.7893 5.41421 18.4142C5.78929 18.0391 6 17.5304 6 17C6 16.4696 5.78929 15.9609 5.41421 15.5858C5.03914 15.2107 4.53043 15 4 15C3.46957 15 2.96086 15.2107 2.58579 15.5858C2.21071 15.9609 2 16.4696 2 17Z"/>
      <path d="M12 21.9997C12 21.9997 8 12.9997 10.5 10.4997C13 7.99973 22 11.9997 22 11.9997"/>

    </svg>
  );
}
