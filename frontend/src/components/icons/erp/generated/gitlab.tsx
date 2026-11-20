import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function GitlabIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M22 13.2899L18.67 3.28989C18.6408 3.21813 18.5924 3.15583 18.53 3.10989C18.4709 3.04985 18.3935 3.01115 18.31 2.99989C18.2279 2.99842 18.1474 3.02292 18.08 3.06989C18.0176 3.11583 17.9692 3.17813 17.94 3.24989L15.68 9.91989H8.32001L6.10001 3.25989C6.08213 3.19252 6.04776 3.13066 6.00001 3.07989C5.92619 3.02205 5.83358 2.99356 5.74001 2.99989C5.65789 2.99842 5.57739 3.02292 5.51001 3.06989C5.44764 3.11583 5.39918 3.17813 5.37001 3.24989L2.00001 13.2899C1.95122 13.439 1.95108 13.5997 1.99961 13.7489C2.04815 13.8981 2.14284 14.028 2.27001 14.1199L12 20.9999L21.69 14.1199C21.8281 14.0372 21.934 13.91 21.9904 13.7592C22.0467 13.6084 22.0501 13.4429 22 13.2899Z"/>

    </svg>
  );
}
