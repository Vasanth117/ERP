import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function RollerCoasterIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M6 19V5"/>
      <path d="M10 18.9998V6.7998"/>
      <path d="M14 19.0002V11.2002"/>
      <path d="M18 5V9"/>
      <path d="M18 19V13"/>
      <path d="M22 19V9"/>
      <path d="M2 19V9C2 7.93913 2.42143 6.92172 3.17157 6.17157C3.92172 5.42143 4.93913 5 6 5C8 5 10 6.33 12 9C14 11.67 16 13 18 13C18.668 12.9994 19.3252 12.8315 19.9117 12.5116C20.4981 12.1917 20.9951 11.73 21.3573 11.1687C21.7195 10.6074 21.9353 9.96436 21.9851 9.29821C22.0349 8.63206 21.9171 7.96404 21.6424 7.35512C21.3677 6.74621 20.9449 6.21578 20.4125 5.81226C19.8801 5.40874 19.2552 5.14497 18.5947 5.04503C17.9342 4.94508 17.2592 5.01214 16.6313 5.24009C16.0034 5.46804 15.4426 5.84962 15 6.35"/>

    </svg>
  );
}
