import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function PaintBucketIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M19 11L11 3L2.40002 11.6C2.03357 11.9739 1.82831 12.4765 1.82831 13C1.82831 13.5235 2.03357 14.0261 2.40002 14.4L7.60002 19.6C8.40002 20.4 9.60002 20.4 10.4 19.6L19 11Z"/>
      <path d="M5 2L10 7"/>
      <path d="M2 13H17"/>
      <path d="M22 20C22 20.5304 21.7893 21.0391 21.4142 21.4142C21.0391 21.7893 20.5304 22 20 22C19.4696 22 18.9609 21.7893 18.5858 21.4142C18.2107 21.0391 18 20.5304 18 20C18 18.4 19.7 17.6 20 16C20.3 17.6 22 18.4 22 20Z"/>

    </svg>
  );
}
