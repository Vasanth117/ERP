import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function AmpersandIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M17.5 12C17.5 16.4 13.9 20 9.5 20C8.30653 20 7.16193 19.5259 6.31802 18.682C5.47411 17.8381 5 16.6935 5 15.5C5 9.5 13 11.5 13 7C13 6.20435 12.6839 5.44129 12.1213 4.87868C11.5587 4.31607 10.7956 4 10 4C9.20435 4 8.44129 4.31607 7.87868 4.87868C7.31607 5.44129 7 6.20435 7 7C7 10 9.5 15.5 19 20"/>
      <path d="M16 12H19"/>

    </svg>
  );
}
