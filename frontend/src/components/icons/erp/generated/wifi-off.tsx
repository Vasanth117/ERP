import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function WifiOffIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M12 20H12.01"/>
      <path d="M8.5 16.4288C9.43464 15.5127 10.6912 14.9995 12 14.9995C13.3088 14.9995 14.5654 15.5127 15.5 16.4288"/>
      <path d="M5 12.8589C6.41803 11.4689 8.21781 10.5324 10.17 10.1689"/>
      <path d="M19 12.8589C18.3979 12.2687 17.7235 11.757 16.993 11.3359"/>
      <path d="M2 8.81976C3.2366 7.71383 4.64809 6.82071 6.177 6.17676"/>
      <path d="M22 8.81991C20.4747 7.45573 18.6864 6.41806 16.7452 5.77074C14.8039 5.12343 12.7508 4.88016 10.712 5.05591"/>
      <path d="M2 2L22 22"/>

    </svg>
  );
}
