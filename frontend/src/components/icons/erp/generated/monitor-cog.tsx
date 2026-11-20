import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function MonitorCogIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M12 17V21"/>
      <path d="M15.2 4.9L14.3 4.5"/>
      <path d="M15.2 7.1001L14.3 7.5001"/>
      <path d="M16.9 3.1998L16.5 2.2998"/>
      <path d="M16.9 8.7998L16.5 9.6998"/>
      <path d="M19.5 2.2998L19.1 3.1998"/>
      <path d="M19.5 9.6998L19.1 8.7998"/>
      <path d="M21.7 4.5L20.8 4.9"/>
      <path d="M21.7 7.5001L20.8 7.1001"/>
      <path d="M22 13V15C22 15.5304 21.7893 16.0391 21.4142 16.4142C21.0391 16.7893 20.5304 17 20 17H4C3.46957 17 2.96086 16.7893 2.58579 16.4142C2.21071 16.0391 2 15.5304 2 15V5C2 4.46957 2.21071 3.96086 2.58579 3.58579C2.96086 3.21071 3.46957 3 4 3H11"/>
      <path d="M8 21H16"/>
      <path d="M15 6C15 6.79565 15.3161 7.55871 15.8787 8.12132C16.4413 8.68393 17.2044 9 18 9C18.7956 9 19.5587 8.68393 20.1213 8.12132C20.6839 7.55871 21 6.79565 21 6C21 5.20435 20.6839 4.44129 20.1213 3.87868C19.5587 3.31607 18.7956 3 18 3C17.2044 3 16.4413 3.31607 15.8787 3.87868C15.3161 4.44129 15 5.20435 15 6Z"/>

    </svg>
  );
}
