import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function FileQuestionIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M12 17H12.01"/>
      <path d="M15 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V20C4 20.5304 4.21071 21.0391 4.58579 21.4142C4.96086 21.7893 5.46957 22 6 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V7L15 2Z"/>
      <path d="M9.09998 8.99992C9.33995 8.33855 9.80475 7.78257 10.4131 7.42915C11.0215 7.07574 11.7347 6.94738 12.4281 7.06653C13.1215 7.18567 13.751 7.54472 14.2065 8.08093C14.662 8.61714 14.9145 9.29638 14.92 9.99992C14.92 11.9999 11.92 12.9999 11.92 12.9999"/>

    </svg>
  );
}
