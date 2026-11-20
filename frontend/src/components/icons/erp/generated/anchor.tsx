import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function AnchorIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M12 22V8"/>
      <path d="M5 12H2C2 14.6522 3.05357 17.1957 4.92893 19.0711C6.8043 20.9464 9.34784 22 12 22C14.6522 22 17.1957 20.9464 19.0711 19.0711C20.9464 17.1957 22 14.6522 22 12H19"/>
      <path d="M9 5C9 5.79565 9.31607 6.55871 9.87868 7.12132C10.4413 7.68393 11.2044 8 12 8C12.7956 8 13.5587 7.68393 14.1213 7.12132C14.6839 6.55871 15 5.79565 15 5C15 4.20435 14.6839 3.44129 14.1213 2.87868C13.5587 2.31607 12.7956 2 12 2C11.2044 2 10.4413 2.31607 9.87868 2.87868C9.31607 3.44129 9 4.20435 9 5Z"/>

    </svg>
  );
}
