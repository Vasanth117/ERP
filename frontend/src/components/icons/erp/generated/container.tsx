import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ContainerIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M22 7.6999C22 7.0999 21.6 6.4999 21.2 6.1999L14.9 2.2999C14.6409 2.15263 14.348 2.0752 14.05 2.0752C13.752 2.0752 13.4591 2.15263 13.2 2.2999L2.9 8.2999C2.4 8.4999 2 9.0999 2 9.6999V16.2999C2 16.7999 2.4 17.4999 2.8 17.7999L9.1 21.6999C9.35908 21.8472 9.65198 21.9246 9.95 21.9246C10.248 21.9246 10.5409 21.8472 10.8 21.6999L21.1 15.6999C21.6 15.3999 22 14.6999 22 14.1999V7.6999Z"/>
      <path d="M9.99998 21.9001V14.0001L2.09998 9.1001"/>
      <path d="M10 14.0001L21.9 7.1001"/>
      <path d="M14 19.8V11.7"/>
      <path d="M18 17.4999V9.3999"/>

    </svg>
  );
}
