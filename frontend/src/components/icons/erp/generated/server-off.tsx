import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ServerOffIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M7 2H20C20.5304 2 21.0391 2.21071 21.4142 2.58579C21.7893 2.96086 22 3.46957 22 4V8C22 8.53043 21.7893 9.03914 21.4142 9.41421C21.0391 9.78929 20.5304 10 20 10H15"/>
      <path d="M10 9.99992L2.5 2.49992C2 1.99992 2 2.49992 2 4.99992V7.99992C2 8.53035 2.21071 9.03906 2.58579 9.41413C2.96086 9.7892 3.46957 9.99992 4 9.99992H10Z"/>
      <path d="M22 17V16C22 15.4696 21.7893 14.9609 21.4142 14.5858C21.0391 14.2107 20.5304 14 20 14H19"/>
      <path d="M4 14C3.46957 14 2.96086 14.2107 2.58579 14.5858C2.21071 14.9609 2 15.4696 2 16V20C2 20.5304 2.21071 21.0391 2.58579 21.4142C2.96086 21.7893 3.46957 22 4 22H20.5L21.5 21.5L22 22L14 14H4Z"/>
      <path d="M6 18H6.01"/>
      <path d="M2 2L22 22"/>

    </svg>
  );
}
