import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function CableCarIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M10 3H10.01"/>
      <path d="M14 2H14.01"/>
      <path d="M2 9L22 4"/>
      <path d="M12 12V6.5"/>
      <path d="M7 12H17C17.7956 12 18.5587 12.3161 19.1213 12.8787C19.6839 13.4413 20 14.2044 20 15V19C20 19.7956 19.6839 20.5587 19.1213 21.1213C18.5587 21.6839 17.7956 22 17 22H7C6.20435 22 5.44129 21.6839 4.87868 21.1213C4.31607 20.5587 4 19.7956 4 19V15C4 14.2044 4.31607 13.4413 4.87868 12.8787C5.44129 12.3161 6.20435 12 7 12Z"/>
      <path d="M9 12V17"/>
      <path d="M15 12V17"/>
      <path d="M4 17H20"/>

    </svg>
  );
}
