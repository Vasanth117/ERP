import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function TriangleRightIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M22 18.0004C22 18.5308 21.7893 19.0395 21.4142 19.4146C21.0391 19.7897 20.5304 20.0004 20 20.0004H2.99999C1.89999 20.0004 1.69999 19.4004 2.59999 18.7004L20.4 4.30039C21.3 3.60039 22 3.90039 22 5.00039V18.0004Z"/>

    </svg>
  );
}
