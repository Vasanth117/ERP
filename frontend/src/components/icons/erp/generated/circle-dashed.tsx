import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function CircleDashedIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M10.1 2.18216C11.355 1.93928 12.645 1.93928 13.9 2.18216"/>
      <path d="M13.9 21.8184C12.645 22.0612 11.355 22.0612 10.1 21.8184"/>
      <path d="M17.609 3.7207C18.6705 4.43993 19.5837 5.35657 20.299 6.4207"/>
      <path d="M2.18201 13.8996C1.93913 12.6446 1.93913 11.3546 2.18201 10.0996"/>
      <path d="M20.279 17.6094C19.5598 18.6708 18.6431 19.5841 17.579 20.2994"/>
      <path d="M21.818 10.0996C22.0609 11.3546 22.0609 12.6446 21.818 13.8996"/>
      <path d="M3.72101 6.39117C4.44023 5.3297 5.35688 4.41645 6.42101 3.70117"/>
      <path d="M6.39099 20.2791C5.32952 19.5599 4.41627 18.6432 3.70099 17.5791"/>

    </svg>
  );
}
