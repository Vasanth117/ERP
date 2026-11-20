import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function NotepadTextDashedIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M8 2V6"/>
      <path d="M12 2V6"/>
      <path d="M16 2V6"/>
      <path d="M16 4H18C18.5304 4 19.0391 4.21071 19.4142 4.58579C19.7893 4.96086 20 5.46957 20 6V8"/>
      <path d="M20 12V14"/>
      <path d="M20 18V20C20 20.5304 19.7893 21.0391 19.4142 21.4142C19.0391 21.7893 18.5304 22 18 22H17"/>
      <path d="M13 22H11"/>
      <path d="M7 22H6C5.46957 22 4.96086 21.7893 4.58579 21.4142C4.21071 21.0391 4 20.5304 4 20V18"/>
      <path d="M4 14V12"/>
      <path d="M4 8V6C4 5.46957 4.21071 4.96086 4.58579 4.58579C4.96086 4.21071 5.46957 4 6 4H8"/>
      <path d="M8 10H14"/>
      <path d="M8 14H16"/>
      <path d="M8 18H13"/>

    </svg>
  );
}
