import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function PlugZapIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M6.30003 20.3C6.523 20.5237 6.78794 20.7013 7.07967 20.8224C7.37139 20.9435 7.68416 21.0059 8.00003 21.0059C8.31591 21.0059 8.62867 20.9435 8.9204 20.8224C9.21212 20.7013 9.47706 20.5237 9.70003 20.3L12 18L6.00003 12L3.70003 14.3C3.47629 14.523 3.29876 14.7879 3.17763 15.0796C3.05649 15.3714 2.99414 15.6841 2.99414 16C2.99414 16.3159 3.05649 16.6286 3.17763 16.9204C3.29876 17.2121 3.47629 17.477 3.70003 17.7L6.30003 20.3Z"/>
      <path d="M2 22L5 19"/>
      <path d="M7.5 13.5L10 11"/>
      <path d="M10.5 16.5L13 14"/>
      <path d="M18 3L14 7H20L16 11"/>

    </svg>
  );
}
