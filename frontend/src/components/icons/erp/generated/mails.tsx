import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function MailsIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M8 4H20C20.5304 4 21.0391 4.21071 21.4142 4.58579C21.7893 4.96086 22 5.46957 22 6V15C22 15.5304 21.7893 16.0391 21.4142 16.4142C21.0391 16.7893 20.5304 17 20 17H8C7.46957 17 6.96086 16.7893 6.58579 16.4142C6.21071 16.0391 6 15.5304 6 15V6C6 5.46957 6.21071 4.96086 6.58579 4.58579C6.96086 4.21071 7.46957 4 8 4Z"/>
      <path d="M22 7L14.9 10.78C14.33 11.08 13.67 11.08 13.1 10.78L6 7"/>
      <path d="M2 8V19C2 20.1 2.9 21 4 21H18"/>

    </svg>
  );
}
