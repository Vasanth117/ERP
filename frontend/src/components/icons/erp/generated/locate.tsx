import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function LocateIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M2 12H5"/>
      <path d="M19 12H22"/>
      <path d="M12 2V5"/>
      <path d="M12 19V22"/>
      <path d="M5 12C5 12.9193 5.18106 13.8295 5.53284 14.6788C5.88463 15.5281 6.40024 16.2997 7.05025 16.9497C7.70026 17.5998 8.47194 18.1154 9.32122 18.4672C10.1705 18.8189 11.0807 19 12 19C12.9193 19 13.8295 18.8189 14.6788 18.4672C15.5281 18.1154 16.2997 17.5998 16.9497 16.9497C17.5998 16.2997 18.1154 15.5281 18.4672 14.6788C18.8189 13.8295 19 12.9193 19 12C19 11.0807 18.8189 10.1705 18.4672 9.32122C18.1154 8.47194 17.5998 7.70026 16.9497 7.05025C16.2997 6.40024 15.5281 5.88463 14.6788 5.53284C13.8295 5.18106 12.9193 5 12 5C11.0807 5 10.1705 5.18106 9.32122 5.53284C8.47194 5.88463 7.70026 6.40024 7.05025 7.05025C6.40024 7.70026 5.88463 8.47194 5.53284 9.32122C5.18106 10.1705 5 11.0807 5 12Z"/>

    </svg>
  );
}
