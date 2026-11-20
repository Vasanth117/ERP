import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ScissorsIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M3 6C3 6.79565 3.31607 7.55871 3.87868 8.12132C4.44129 8.68393 5.20435 9 6 9C6.79565 9 7.55871 8.68393 8.12132 8.12132C8.68393 7.55871 9 6.79565 9 6C9 5.20435 8.68393 4.44129 8.12132 3.87868C7.55871 3.31607 6.79565 3 6 3C5.20435 3 4.44129 3.31607 3.87868 3.87868C3.31607 4.44129 3 5.20435 3 6Z"/>
      <path d="M8.12 8.12012L12 12.0001"/>
      <path d="M20 4L8.12 15.88"/>
      <path d="M3 18C3 18.7956 3.31607 19.5587 3.87868 20.1213C4.44129 20.6839 5.20435 21 6 21C6.79565 21 7.55871 20.6839 8.12132 20.1213C8.68393 19.5587 9 18.7956 9 18C9 17.2044 8.68393 16.4413 8.12132 15.8787C7.55871 15.3161 6.79565 15 6 15C5.20435 15 4.44129 15.3161 3.87868 15.8787C3.31607 16.4413 3 17.2044 3 18Z"/>
      <path d="M14.8 14.7998L20 19.9998"/>

    </svg>
  );
}
