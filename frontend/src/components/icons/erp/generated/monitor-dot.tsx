import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function MonitorDotIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M16 6C16 6.79565 16.3161 7.55871 16.8787 8.12132C17.4413 8.68393 18.2044 9 19 9C19.7956 9 20.5587 8.68393 21.1213 8.12132C21.6839 7.55871 22 6.79565 22 6C22 5.20435 21.6839 4.44129 21.1213 3.87868C20.5587 3.31607 19.7956 3 19 3C18.2044 3 17.4413 3.31607 16.8787 3.87868C16.3161 4.44129 16 5.20435 16 6Z"/>
      <path d="M22 12V15C22 15.5304 21.7893 16.0391 21.4142 16.4142C21.0391 16.7893 20.5304 17 20 17H4C3.46957 17 2.96086 16.7893 2.58579 16.4142C2.21071 16.0391 2 15.5304 2 15V5C2 4.46957 2.21071 3.96086 2.58579 3.58579C2.96086 3.21071 3.46957 3 4 3H13"/>
      <path d="M12 17V21"/>
      <path d="M8 21H16"/>

    </svg>
  );
}
