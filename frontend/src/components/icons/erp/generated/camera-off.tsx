import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function CameraOffIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M2 2L22 22"/>
      <path d="M7 7H4C3.46957 7 2.96086 7.21071 2.58579 7.58579C2.21071 7.96086 2 8.46957 2 9V18C2 18.5304 2.21071 19.0391 2.58579 19.4142C2.96086 19.7893 3.46957 20 4 20H20"/>
      <path d="M9.5 4H14.5L17 7H20C20.5304 7 21.0391 7.21071 21.4142 7.58579C21.7893 7.96086 22 8.46957 22 9V16.5"/>
      <path d="M14.121 15.1209C13.8455 15.4122 13.5143 15.6453 13.1471 15.8065C12.78 15.9676 12.3842 16.0535 11.9832 16.0591C11.5823 16.0647 11.1843 15.9898 10.8128 15.8389C10.4413 15.6881 10.1037 15.4642 9.82021 15.1807C9.53667 14.8972 9.31285 14.5596 9.16197 14.1881C9.0111 13.8166 8.93624 13.4186 8.94182 13.0177C8.94739 12.6167 9.03329 12.2209 9.19444 11.8538C9.35558 11.4866 9.5887 11.1554 9.88002 10.8799"/>

    </svg>
  );
}
