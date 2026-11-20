import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ImageUpscaleIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M16 3H21V8"/>
      <path d="M17 21H19C19.5304 21 20.0391 20.7893 20.4142 20.4142C20.7893 20.0391 21 19.5304 21 19"/>
      <path d="M21 12V15"/>
      <path d="M21 3L16 8"/>
      <path d="M3 7V5C3 4.46957 3.21071 3.96086 3.58579 3.58579C3.96086 3.21071 4.46957 3 5 3"/>
      <path d="M5 20.9998L9.144 16.8558C9.25637 16.7433 9.38981 16.6541 9.53669 16.5932C9.68357 16.5323 9.84101 16.501 10 16.501C10.159 16.501 10.3164 16.5323 10.4633 16.5932C10.6102 16.6541 10.7436 16.7433 10.856 16.8558L13 18.9998"/>
      <path d="M9 3H12"/>
      <path d="M4 11H12C12.2652 11 12.5196 11.1054 12.7071 11.2929C12.8946 11.4804 13 11.7348 13 12V20C13 20.2652 12.8946 20.5196 12.7071 20.7071C12.5196 20.8946 12.2652 21 12 21H4C3.73478 21 3.48043 20.8946 3.29289 20.7071C3.10536 20.5196 3 20.2652 3 20V12C3 11.7348 3.10536 11.4804 3.29289 11.2929C3.48043 11.1054 3.73478 11 4 11Z"/>

    </svg>
  );
}
