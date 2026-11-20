import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ShuffleIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M18 14L22 18L18 22"/>
      <path d="M18 2L22 6L18 10"/>
      <path d="M2 18.0001H3.973C4.61949 18.0045 5.25742 17.8522 5.83215 17.5561C6.40687 17.26 6.90127 16.829 7.273 16.3001L12.727 7.70009C13.0987 7.17114 13.5931 6.74017 14.1679 6.4441C14.7426 6.14803 15.3805 5.99568 16.027 6.00009H22"/>
      <path d="M2 6.0001H3.972C4.71746 5.99491 5.44954 6.19814 6.08564 6.58687C6.72174 6.9756 7.23655 7.53436 7.572 8.2001"/>
      <path d="M22 18H15.959C15.3036 17.9933 14.6598 17.8257 14.0844 17.5118C13.5089 17.1979 13.0195 16.7474 12.659 16.2L12.3 15.75"/>

    </svg>
  );
}
